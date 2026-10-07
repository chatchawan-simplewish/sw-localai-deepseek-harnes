import { createHash, timingSafeEqual } from 'node:crypto';
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { z } from 'zod';

const HOSTS = ['prox-01', 'prox-03', 'prox-04'];
const MAX_OUTPUT_BYTES = 128 * 1024;
const SSH_CONFIG = '/etc/dsh-infra-admin/ssh_config';
const TOKEN = Buffer.from(process.env.MCP_INFRA_ADMIN_TOKEN ?? '', 'utf8');

if (TOKEN.length === 0) throw new Error('MCP_INFRA_ADMIN_TOKEN must be set');

function isAuthorized(header) {
  if (typeof header !== 'string' || !header.startsWith('Bearer ')) return false;
  const candidate = Buffer.from(header.slice('Bearer '.length), 'utf8');
  return candidate.length === TOKEN.length && timingSafeEqual(candidate, TOKEN);
}

function runSsh(target, command, timeoutSeconds = 30) {
  return new Promise((resolve) => {
    const child = spawn('/usr/bin/ssh', ['-F', SSH_CONFIG, target, command], { stdio: ['ignore', 'pipe', 'pipe'] });
    let output = Buffer.alloc(0);
    let outputTruncated = false;
    let timedOut = false;
    const append = (chunk) => {
      const remaining = MAX_OUTPUT_BYTES - output.length;
      if (remaining <= 0) {
        outputTruncated = true;
        return;
      }
      if (chunk.length > remaining) {
        outputTruncated = true;
        output = Buffer.concat([output, chunk.subarray(0, remaining)]);
        return;
      }
      output = Buffer.concat([output, chunk]);
    };
    child.stdout.on('data', append);
    child.stderr.on('data', append);
    child.on('error', (error) => append(Buffer.from(error.message)));
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill('SIGTERM');
    }, timeoutSeconds * 1000);
    child.on('close', (code) => {
      clearTimeout(timer);
      const exitStatus = timedOut ? 'timed_out' : code;
      const clientWaitStatus = timedOut ? 'timed_out' : 'completed';
      const remoteOutcome = timedOut ? 'unknown' : 'ssh_command_exited';
      console.info(JSON.stringify({ target, exitStatus, clientWaitStatus, remoteOutcome, outputTruncated, commandDigest: createHash('sha256').update(command).digest('hex') }));
      resolve({
        target,
        exitStatus,
        clientWaitStatus,
        remoteOutcome,
        ...(timedOut && { retryInstruction: 'Inspect remote task state before retrying; ending the SSH client wait does not cancel remote work.' }),
        outputTruncated,
        output: output.toString('utf8'),
      });
    });
  });
}

function text(result) {
  return { content: [{ type: 'text', text: JSON.stringify(result) }] };
}

function broker() {
  const server = new McpServer({ name: 'infrastructure-admin', version: '1.0.0' });
  server.registerTool('infrastructure_inventory', { description: 'List Proxmox VMs on every fixed infrastructure host.' }, async () =>
    text(await Promise.all(HOSTS.map((target) => runSsh(target, 'pvesh get /cluster/resources --type vm')))),
  );
  server.registerTool('run_infrastructure_command', {
    description: 'Run an owner-authorized command on one fixed infrastructure host. Full Proxmox-root administration trusts the caller with potentially sensitive command output. timeoutSeconds limits only the local SSH client wait: a timeout returns remoteOutcome: unknown, may leave remote work running, and requires remote task-state inspection before retrying.',
    inputSchema: {
      target: z.enum(HOSTS),
      command: z.string().min(1),
      timeoutSeconds: z.number().int().min(1).max(300).optional(),
    },
  }, async ({ target, command, timeoutSeconds }) => text(await runSsh(target, command, timeoutSeconds)));
  return server;
}

createServer(async (request, response) => {
  if (!isAuthorized(request.headers.authorization)) {
    response.writeHead(401, { 'WWW-Authenticate': 'Bearer' });
    response.end();
    return;
  }
  if (request.url !== '/mcp') {
    response.writeHead(404);
    response.end();
    return;
  }
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  response.on('close', () => transport.close());
  try {
    await broker().connect(transport);
    await transport.handleRequest(request, response);
  } catch {
    console.error('MCP request failed');
    if (!response.headersSent) response.writeHead(500);
    response.end();
  }
}).listen(8182, '127.0.0.1');
