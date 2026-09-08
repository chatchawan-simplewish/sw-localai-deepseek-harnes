#!/usr/bin/env python3
"""One isolated candidate attempt. Default prints contract; --apply is explicit."""
import argparse
import collections
import hashlib
import json
import os
import posixpath as pp
import re
import shlex
import signal
import socket
import stat
import subprocess
import sys
import time
import uuid

HOME = '/home/dsh/.dsh-profiles/vm105-provider-v1'
OLD = '/home/dsh/.dsh'
INSTALL = '/opt/deepseek-harness'
PACKAGE = INSTALL + '/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh'
UNIT = 'deepseek-harness-candidate-smoke-20260909.service'
PILOT = 'deepseek-harness.service'
FORBIDDEN = {'system.posix_acl_access', 'system.posix_acl_default', 'security.capability'}
FILES = {
    'profiles/web/package.json': '210068ddb9ebc4cdf395ebb53020be6ccaaedb917e74dae16296d62394626398',
    'profiles/web/pnpm-workspace.yaml': '95258a5c24e8cdd4eeb341febcdf58c619293a86859888447c6d556cce99d174',
    'profiles/web/cordis.yml': '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570',
    'profiles/web/cordis.patch.yml': '7c4b50b071a07a705b817a689fb02b6e1b616aae159fa47572828bcefece99cb',
}
PROPERTIES = {
    'User': 'dsh', 'Group': 'dsh', 'UMask': '0077', 'WorkingDirectory': '/srv/dsh/workspaces',
    'ProtectSystem': 'strict', 'ProtectHome': 'no', 'ReadWritePaths': HOME,
    'InaccessiblePaths': OLD, 'PrivateTmp': 'yes', 'NoNewPrivileges': 'yes',
    'PrivateNetwork': 'yes', 'RestrictAddressFamilies': 'AF_INET AF_INET6',
    'RuntimeMaxSec': '120', 'TimeoutStartSec': '30', 'TimeoutStopSec': '15',
    'Restart': 'no', 'MemoryMax': '512M', 'CPUQuota': '100%', 'TasksMax': '128',
    'KillMode': 'control-group', 'StandardInput': 'null', 'StandardOutput': 'null', 'StandardError': 'null',
}
EFFECTIVE = {k: v for k, v in PROPERTIES.items()
             if k not in {'RuntimeMaxSec', 'TimeoutStartSec', 'TimeoutStopSec', 'MemoryMax', 'CPUQuota'}}
EFFECTIVE.update({'RuntimeMaxUSec': '2min', 'TimeoutStartUSec': '30s', 'TimeoutStopUSec': '15s',
                  'MemoryMax': '536870912', 'CPUQuotaPerSecUSec': '1s', 'Transient': 'yes',
                  'PassEnvironment': '', 'JoinsNamespaceOf': '', 'Sockets': ''})
ENV_SOURCE_PROOF = 'ABSENT_SOURCE_VERIFIED'
KNOWN_MAPPINGS = {'@deepseek-ai/dsh': {'logical': '/opt/deepseek-harness/node_modules/@deepseek-ai/dsh',
                      'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh'},
 '@deepseek-ai/dsh-base': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-base',
                           'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-base'},
 '@deepseek-ai/dsh-web-app': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-web-app',
                              'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app'},
 '@deepseek-ai/dsh-credentials-local': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-credentials-local',
                                        'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-credentials-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+ds_7bb67d14430a2d1ff3cabd2ed2468913/node_modules/@deepseek-ai/dsh-credentials-local'},
 '@deepseek-ai/dsh-settings-file': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-settings-file',
                                    'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-settings-file@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-at_07dac851674f547bcb0fed2f2776d133/node_modules/@deepseek-ai/dsh-settings-file'},
 '@deepseek-ai/dsh-session-persistence-jsonl': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-session-persistence-jsonl',
                                                'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-persistence-jsonl@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepse_14f57a8dc717fa4ab0d46db3acee4cf9/node_modules/@deepseek-ai/dsh-session-persistence-jsonl'},
 '@deepseek-ai/dsh-session-query-sqlite': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-session-query-sqlite',
                                           'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-query-sqlite@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai_8ad53b91c340c6b558e2b3a4406f8efa/node_modules/@deepseek-ai/dsh-session-query-sqlite'},
 '@deepseek-ai/dsh-attachment-local': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-attachment-local',
                                       'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-attachment-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh_48db1ca9b536b07a9b9b8a3fb21f8dd4/node_modules/@deepseek-ai/dsh-attachment-local'},
 '@deepseek-ai/dsh-spill-local': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-spill-local',
                                  'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-spill-local@0.1.1-rc.2_7314b9cfa55168b22f8f6fda35aa8983/node_modules/@deepseek-ai/dsh-spill-local'},
 '@deepseek-ai/dsh-storage-json': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-storage-json',
                                   'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-json@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-inv_59f569bce1a393f7830e8147447e2db0/node_modules/@deepseek-ai/dsh-storage-json'},
 '@deepseek-ai/dsh-workspace': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-workspace',
                                'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-workspace@0.1.1-rc.2_ca1aef6913f66bb64a14405a8170db89/node_modules/@deepseek-ai/dsh-workspace'},
 '@deepseek-ai/dsh-storage-domain': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-storage-domain',
                                     'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-domain@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_1dd5e89577ac0f175d4162432caf3a24/node_modules/@deepseek-ai/dsh-storage-domain'},
 '@deepseek-ai/dsh-home-paths': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-home-paths',
                                 'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-home-paths@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invar_260f8dde1d5adbe84fd51b779f4f83da/node_modules/@deepseek-ai/dsh-home-paths'},
 '@deepseek-ai/dsh-app-boot': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-app-boot',
                               'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot'},
 '@deepseek-ai/dsh-jobs-local': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-jobs-local',
                                 'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-jobs-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-agent_fa0dcc68596217609c256ec409a4fd14/node_modules/@deepseek-ai/dsh-jobs-local'},
 '@deepseek-ai/dsh-session-telemetry-otel': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-session-telemetry-otel',
                                             'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-telemetry-otel@0.1.1-rc.2_0e329a50b6fe6a15de6a41bb5c1b84f9/node_modules/@deepseek-ai/dsh-session-telemetry-otel'},
 '@deepseek-ai/dsh-skill-filesystem': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-skill-filesystem',
                                       'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill-filesystem@0.1.1-rc.2_48868494a4b9bcea1966f12a762e8376/node_modules/@deepseek-ai/dsh-skill-filesystem'},
 '@deepseek-ai/dsh-skill': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-skill',
                            'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invariants_59a2d92d9f246f83337b4268751f40ea/node_modules/@deepseek-ai/dsh-skill'},
 '@deepseek-ai/dsh-agent-presets': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-agent-presets',
                                    'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-presets@0.1.1-rc.2_5200ead8959daeaefdf3dd69ba905368/node_modules/@deepseek-ai/dsh-agent-presets'},
 '@deepseek-ai/dsh-persona': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh-persona',
                              'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-persona@0.1.1-rc.2_c46449525c16bef5ec3490eab6722d56/node_modules/@deepseek-ai/dsh-persona'},
 '@deepseek-ai/dsh-llm': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-llm',
                          'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-attachment@0_de8559ed89b7370843bac1bad71a6196/node_modules/@deepseek-ai/dsh-llm'},
 '@deepseek-ai/dsh-llm-pi-ai': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-llm-pi-ai',
                                'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai'},
 '@deepseek-ai/dsh-llm-deepseek': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-llm-deepseek',
                                   'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-deepseek@0.1.1-rc.2_a4f32a8d2888fcc753211ed9471efdc6/node_modules/@deepseek-ai/dsh-llm-deepseek'},
 '@deepseek-ai/dsh-agent-default-model': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-agent-default-model',
                                          'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-default-model@0.1.1-rc.2_cffd0b3811dd3fb50ded7f3d23c3fd53/node_modules/@deepseek-ai/dsh-agent-default-model'},
 '@deepseek-ai/dsh-api-gateway': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-api-gateway',
                                  'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-gateway@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-clie_589a9bcbaefa93b267d467a3607f6172/node_modules/@deepseek-ai/dsh-api-gateway'},
 '@deepseek-ai/dsh-api-remotes': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-api-remotes',
                                  'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-remotes@0.1.1-rc.2_0037c360ed8ef45e74e856e82932995e/node_modules/@deepseek-ai/dsh-api-remotes'},
 '@deepseek-ai/dsh-host-apiproxy': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-host-apiproxy',
                                    'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-apiproxy@0.1.1-rc.2_7a1c54e2b954eca6f88bad802758761b/node_modules/@deepseek-ai/dsh-host-apiproxy'},
 '@deepseek-ai/dsh-client-ui-settings-models': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-client-ui-settings-models',
                                                'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models'},
 '@deepseek-ai/dsh-host-webserver': {'logical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-host-webserver',
                                     'canonical': '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-webserver@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_58d11404f8dbf7a916bca46d37e27714/node_modules/@deepseek-ai/dsh-host-webserver'}}
# Filled from the reviewed public-source receipt, never runtime-generated state.
SOURCE_PINS = {'/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh/package.json': 'dc930c0b18158f49ae3753ceaf6b1b7ae71dc6c8f45c85a2d679b142024addf7',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh/config/agent-presets/standard/agent.cordis.yml': 'fa14feb98daef20b810fef30bb7239a89a786de3c45c602b37743f7100d9a5af',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-base/package.json': '35d203246e9c2a8e623da058cd9b1527252b6c4b4bf2acc56f5233a70db676df',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-base@0.1.1-rc.2_b6700999316794178df1eb7155dc0a46/node_modules/@deepseek-ai/dsh-base/cordis.patch.yml': '9870a518274194c0e1ebd870cee2737fbc2ffc04ae36887871ffe6fcf74beac1',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app/package.json': 'f1ab1f51022e56adae15889764001aed390da0d647db08313d07b571265a27f1',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app/cordis.patch.yml': '7889b655be3809dd21e3c59023f8510e6e8425f6f37616e4ba20389f2e938dda',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-credentials-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+ds_7bb67d14430a2d1ff3cabd2ed2468913/node_modules/@deepseek-ai/dsh-credentials-local/package.json': 'db3521c031061dddf4eebbd28cea8063b4dddd4007d530e2e1def5ff86dd757e',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-credentials-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+ds_7bb67d14430a2d1ff3cabd2ed2468913/node_modules/@deepseek-ai/dsh-credentials-local/lib/index.js': '1688f17801d5809abace4ef6228b771625a0153c043d7d4dba21b398ec4056eb',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-settings-file@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-at_07dac851674f547bcb0fed2f2776d133/node_modules/@deepseek-ai/dsh-settings-file/package.json': '2221515504477467b2a0b26a1c64522426b269a0dcd955e198363fb333ea3399',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-settings-file@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-at_07dac851674f547bcb0fed2f2776d133/node_modules/@deepseek-ai/dsh-settings-file/lib/index.js': '524d02699bc9ce5b5db89aac944a5a4ea3b8e9daf89b298f02e1eb805673a339',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-persistence-jsonl@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepse_14f57a8dc717fa4ab0d46db3acee4cf9/node_modules/@deepseek-ai/dsh-session-persistence-jsonl/package.json': 'c4214db638bacee636f777e2b4cbc4940bf78deaa892037934e42392d83e279d',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-persistence-jsonl@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepse_14f57a8dc717fa4ab0d46db3acee4cf9/node_modules/@deepseek-ai/dsh-session-persistence-jsonl/lib/index.js': '8b6ebc4509a3e969ab3ad6e0dfb553ae4861e5b101831afed23e593d148d97f3',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-query-sqlite@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai_8ad53b91c340c6b558e2b3a4406f8efa/node_modules/@deepseek-ai/dsh-session-query-sqlite/package.json': '1af230f33d67c93e69af9f50fa421ec635b074ade08ce138a183fe86cc2d3d7a',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-query-sqlite@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai_8ad53b91c340c6b558e2b3a4406f8efa/node_modules/@deepseek-ai/dsh-session-query-sqlite/lib/index.js': 'd35c13881eeb9d393fa3a21acaafa6277692e77f90e579ea62a95d6ea0cf370a',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-attachment-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh_48db1ca9b536b07a9b9b8a3fb21f8dd4/node_modules/@deepseek-ai/dsh-attachment-local/package.json': '207ac2fb21254ba93ad585b147bd80a6ff869f28cbf731abcfdbc3a0645fa0f6',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-attachment-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh_48db1ca9b536b07a9b9b8a3fb21f8dd4/node_modules/@deepseek-ai/dsh-attachment-local/lib/index.js': '2d2be7d22cf89895e281489158a2f4c9984497dfcb880ad88b8740e2afec7e76',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-spill-local@0.1.1-rc.2_7314b9cfa55168b22f8f6fda35aa8983/node_modules/@deepseek-ai/dsh-spill-local/package.json': '27707cc1e7746ccf97fb292cc82dd6d14c74f4b5613d8710e320f25f2a6d4e95',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-spill-local@0.1.1-rc.2_7314b9cfa55168b22f8f6fda35aa8983/node_modules/@deepseek-ai/dsh-spill-local/lib/index.js': 'ae92f47942cf63e656c409b3729fe5bdf22e232ec5d05fd14bc9f642b2eb2b0b',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-json@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-inv_59f569bce1a393f7830e8147447e2db0/node_modules/@deepseek-ai/dsh-storage-json/package.json': 'ad83e2b0a6389bb685e74ade1dfe5b4c55a4fb5f2ad94ab12c62f814eee3edd9',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-json@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-inv_59f569bce1a393f7830e8147447e2db0/node_modules/@deepseek-ai/dsh-storage-json/lib/index.js': '563bf17d4060fd280b746b13a03b9b843bf702e4229be73a4397657f75bc0db1',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-workspace@0.1.1-rc.2_ca1aef6913f66bb64a14405a8170db89/node_modules/@deepseek-ai/dsh-workspace/package.json': '0dbf7f622e4b7d930734135368907ed8256a707fab6f990582444772a78e790f',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-workspace@0.1.1-rc.2_ca1aef6913f66bb64a14405a8170db89/node_modules/@deepseek-ai/dsh-workspace/lib/index.js': 'd53e71d931937066ff20440afcff911ced09cefb8a0f3d024348b0e5248d4c74',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-domain@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_1dd5e89577ac0f175d4162432caf3a24/node_modules/@deepseek-ai/dsh-storage-domain/package.json': 'bce55a9b0118d795e950e5aed10cbae55b407b491f7d85d909a0410d0f97a182',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-storage-domain@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_1dd5e89577ac0f175d4162432caf3a24/node_modules/@deepseek-ai/dsh-storage-domain/lib/index.js': '604703d7f461001c95be48536a0f2b76ed8174dec4cba5bf1456a200c47ee72b',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-home-paths@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invar_260f8dde1d5adbe84fd51b779f4f83da/node_modules/@deepseek-ai/dsh-home-paths/package.json': '736ff71c95173d31fb53ebe68451eff978c11b5b747cca6621d86a4504f78e9c',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-home-paths@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invar_260f8dde1d5adbe84fd51b779f4f83da/node_modules/@deepseek-ai/dsh-home-paths/lib/index.js': 'b82aa631aa4bfdd5b02c67d48fce455b2ca73cbf66d2b7096a336b3800914340',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot/package.json': 'ccf455c20e4b20687429dc33cac6857630bce5fe76be483bf2871952ae725c47',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-app-boot@0.1.1-rc.2_d7ed335ddbfb7670edc51bd2c8928580/node_modules/@deepseek-ai/dsh-app-boot/lib/index.js': '9d4b7f214cd35b3e8ce4e027b12cca34a416d355577aeacbf08a5b324f0cabb6',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-jobs-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-agent_fa0dcc68596217609c256ec409a4fd14/node_modules/@deepseek-ai/dsh-jobs-local/package.json': 'd281a711241b290de8e63952c91556db1e69c242768116f9f84c51e3b397d317',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-jobs-local@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-agent_fa0dcc68596217609c256ec409a4fd14/node_modules/@deepseek-ai/dsh-jobs-local/lib/index.js': 'fa4d847d0e7d99364ba875c97f45c2f8b81e51d8a33de0fe6af54acdeb1936a2',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-telemetry-otel@0.1.1-rc.2_0e329a50b6fe6a15de6a41bb5c1b84f9/node_modules/@deepseek-ai/dsh-session-telemetry-otel/package.json': 'ac1484a557fc10f8d0598e2d754895e1b5143edaac7a73c022da639c3e04256d',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-session-telemetry-otel@0.1.1-rc.2_0e329a50b6fe6a15de6a41bb5c1b84f9/node_modules/@deepseek-ai/dsh-session-telemetry-otel/lib/index.js': '22f031eccb0add4265b719a1ce50ae5a4c01d61c0ee3229fa3ebe7158e5e161a',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill-filesystem@0.1.1-rc.2_48868494a4b9bcea1966f12a762e8376/node_modules/@deepseek-ai/dsh-skill-filesystem/package.json': 'f0a4bd7e17b72ad22d03509d954acbe1119862363f032d4faa79b02ce3e72f83',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill-filesystem@0.1.1-rc.2_48868494a4b9bcea1966f12a762e8376/node_modules/@deepseek-ai/dsh-skill-filesystem/lib/index.js': '1aea87781ba5b4d44c7cfd6184d933a1c171a3fd2791456b65ebfc8b255f1221',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invariants_59a2d92d9f246f83337b4268751f40ea/node_modules/@deepseek-ai/dsh-skill/package.json': 'be09a8c49f4a38be29be3b30258c1c0455b5fabc27622f1bb6d5ab317db5adb1',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-skill@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-invariants_59a2d92d9f246f83337b4268751f40ea/node_modules/@deepseek-ai/dsh-skill/lib/index.js': '5402787cbc95b4586e2c3aa4b0129e91094ad368b428aa19bcbbd8553bbfa9d7',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-presets@0.1.1-rc.2_5200ead8959daeaefdf3dd69ba905368/node_modules/@deepseek-ai/dsh-agent-presets/package.json': '2074d078b3945c3a75d9483ce3aaec5ce28c377a6a27d63aef16e12fbd0907ee',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-presets@0.1.1-rc.2_5200ead8959daeaefdf3dd69ba905368/node_modules/@deepseek-ai/dsh-agent-presets/lib/index.js': 'a0b417514e3d285ad5fef74867e8049af333ebdec6e4d7639e388aa0903e0039',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-persona@0.1.1-rc.2_c46449525c16bef5ec3490eab6722d56/node_modules/@deepseek-ai/dsh-persona/package.json': 'a84fbb0919c92b6a3e04b099cf4dc82587445c901eeab6845ad078e417176bf6',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-persona@0.1.1-rc.2_c46449525c16bef5ec3490eab6722d56/node_modules/@deepseek-ai/dsh-persona/lib/index.js': '37a223d0c44fac7fd9d69f55b972828b177db7092fc45302c8b1938e595b9ace',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-attachment@0_de8559ed89b7370843bac1bad71a6196/node_modules/@deepseek-ai/dsh-llm/package.json': '252de11f9af2a92e2e2eb26dc4e80f7b6313586a96ffce16069435b536952cf6',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-attachment@0_de8559ed89b7370843bac1bad71a6196/node_modules/@deepseek-ai/dsh-llm/lib/index.js': '90de54c106866d9333ddc312176e14df75e7c5ee1d6e54443174a827302276fd',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai/package.json': 'b50f77d01dbdffbee612f9969903952c131956e5b28d806c7c82a7f715753f89',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-pi-ai@0.1.1-rc.2_236ec8963c16cce3286da2b293de8170/node_modules/@deepseek-ai/dsh-llm-pi-ai/lib/index.js': 'e183a9cdde703b47485410bd68d247c8becdb277c390f0f91c6dd28718d350e2',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-deepseek@0.1.1-rc.2_a4f32a8d2888fcc753211ed9471efdc6/node_modules/@deepseek-ai/dsh-llm-deepseek/package.json': '4d919cec96dd511db44bfc9eee26bdba19dfaaf9eb2ef5cd2788e6d385be1cd3',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-llm-deepseek@0.1.1-rc.2_a4f32a8d2888fcc753211ed9471efdc6/node_modules/@deepseek-ai/dsh-llm-deepseek/lib/index.js': 'eed9492246cc6451f060de211768d3128388046478deae7f1959de7cde56ea82',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-default-model@0.1.1-rc.2_cffd0b3811dd3fb50ded7f3d23c3fd53/node_modules/@deepseek-ai/dsh-agent-default-model/package.json': '584001c0295a60b907c6118eb7f5da29ed85095d563e19669736d87536d08cd0',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-agent-default-model@0.1.1-rc.2_cffd0b3811dd3fb50ded7f3d23c3fd53/node_modules/@deepseek-ai/dsh-agent-default-model/lib/index.js': '3f9ec5b953658fa1d0b3684b404a8da62ed61b5770ca8dd6b72ce937bae21ecf',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-gateway@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-clie_589a9bcbaefa93b267d467a3607f6172/node_modules/@deepseek-ai/dsh-api-gateway/package.json': '2fa7595b121c14805a4fc1e83c0cc0ceff5660f21c995a93a30e1dd5ea543652',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-gateway@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-clie_589a9bcbaefa93b267d467a3607f6172/node_modules/@deepseek-ai/dsh-api-gateway/lib/index.js': '266fd319e360e9237382be7c180f83b60e1706740b652df768189bae8fc87798',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-remotes@0.1.1-rc.2_0037c360ed8ef45e74e856e82932995e/node_modules/@deepseek-ai/dsh-api-remotes/package.json': 'c659c35186ac4503ff34264ae09b89986cc8fa8351330b9089f5b0a3d6ce698e',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-api-remotes@0.1.1-rc.2_0037c360ed8ef45e74e856e82932995e/node_modules/@deepseek-ai/dsh-api-remotes/lib/index.js': '5406e17c29e42b81ebb8c36030a67de3db19d4d94bace10052b924d72a10e756',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-apiproxy@0.1.1-rc.2_7a1c54e2b954eca6f88bad802758761b/node_modules/@deepseek-ai/dsh-host-apiproxy/package.json': '156d33df741f8cad7ccce2ade30eb6ca241001a5cb68510423dcd99804b6275d',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-apiproxy@0.1.1-rc.2_7a1c54e2b954eca6f88bad802758761b/node_modules/@deepseek-ai/dsh-host-apiproxy/lib/index.js': '8e32ffc951f499849c155e30cb30813af5ed7abb11008653125092299b693d9f',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models/package.json': '050fcc1cadb0e6bcb8bada85039a636864ebfea16228212d1ffd07def3fe8818',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-client-ui-settings-models@0.1.1-rc.2_6ea45dce772d8d764ff9d4e073210778/node_modules/@deepseek-ai/dsh-client-ui-settings-models/lib/client.js': 'c3b9a2d2d074c600c10553a4b15e294082f5851dd4a834d06ddb268b310d18de',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh/lib/bin.js': 'c0226687bb20f45c603ec6fe50f3de16d1c3510c3a803304ec575ef9bc366c62',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh/lib/profile-boot-BnJoK_kl.js': '778c5b338674d986a49972be920c965d28b2c8cac85364ae77f8587070397663',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh@0.1.1-rc.2_7adf779e9bedfb2e97ced92905792931/node_modules/@deepseek-ai/dsh/lib/profile-boot-DG5t9aNs.js': 'f83ffea6a4d30cfbe02b41dabcc05104c4ad27bf79c74f601f0ddb6ccdf88969',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app/lib/index.js': 'b824bfc687db3369cacb23a7a62bceecc936bd8b4c7a4b0bc6b50ad460bd0fda',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-web-app@0.1.1-rc.2_ce3874dffedb66ab726b823cc1dadab8/node_modules/@deepseek-ai/dsh-web-app/lib/startup.js': '95a47053483fbe8ec86711369b8791bccb592c303fcc89300458a4bd07c6c252',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-webserver@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_58d11404f8dbf7a916bca46d37e27714/node_modules/@deepseek-ai/dsh-host-webserver/package.json': '163db0522737b595a6d4054252548960fb692b931071ca36bdd70a504ae1f35b',
 '/opt/deepseek-harness/node_modules/.pnpm/@deepseek-ai+dsh-host-webserver@0.1.1-rc.2_@deepseek-ai+cordis@4.0.1_@deepseek-ai+dsh-i_58d11404f8dbf7a916bca46d37e27714/node_modules/@deepseek-ai/dsh-host-webserver/lib/index.js': '4edcb43fe7427753863338a2f3543ef9023fc7a1156143f707007cce62f7cd6c'}


class Blocked(Exception):
    pass


def require(ok, code):
    if not ok:
        raise Blocked(code)


def validate_selector(env, path):
    require(env == {'DSH_HOME': HOME, 'HOME': '/home/dsh', 'PATH': path}, 'SELECTOR_OR_ENVIRONMENT')


def validate_listener(rows, inodes):
    require(len(rows) == 1 and rows[0][0] == '0100007F:0C09' and rows[0][1] in inodes,
            'LISTENER_OWNERSHIP')


def validate_owned(properties, owner):
    require(owner is not None and properties.get('InvocationID') == owner[0]
            and properties.get('Description') == owner[1], 'CLEANUP_OWNERSHIP')


def snapshot(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def bounded_read(fd, limit):
    data = b''
    while len(data) <= limit:
        chunk = os.read(fd, min(65536, limit + 1 - len(data)))
        if not chunk:
            return data
        data += chunk
    raise Blocked('READ_BOUND')


class Trusted:
    """Held nofollow descriptors and explicitly validated installed symlinks."""
    def __init__(self):
        self.held = {}
        self.links = {}

    def open(self, path, file=False):
        require(path.startswith('/') and pp.normpath(path) == path, 'TRUST_PATH')
        if path in self.held:
            return self.held[path][0]
        parent = None if path == '/' else self.open(pp.dirname(path))
        fd = os.open('/' if path == '/' else pp.basename(path), os.O_RDONLY | os.O_CLOEXEC |
                     os.O_NOFOLLOW | (os.O_NONBLOCK if file else os.O_DIRECTORY), dir_fd=parent)
        s = os.fstat(fd)
        self.held[path] = (fd, snapshot(s), file)
        require((s.st_uid, s.st_gid) == (0, 0) and not s.st_mode & 0o022, 'TRUST_OWNER_MODE')
        require(stat.S_ISREG(s.st_mode) if file else stat.S_ISDIR(s.st_mode), 'TRUST_TYPE')
        require(not file or s.st_nlink >= 1, 'TRUST_LINK_COUNT')
        require(not FORBIDDEN.intersection(os.listxattr(fd)), 'TRUST_ATTRIBUTES')
        return fd

    def resolve(self, path, installation=True):
        require(not installation or path == INSTALL or path.startswith(INSTALL + '/'), 'INSTALL_ESCAPE')
        pending, current, count = collections.deque(path.strip('/').split('/')), '/', 0
        while pending:
            part = pending.popleft()
            parent = self.open(current)
            item = pp.join(current, part)
            s = os.stat(part, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(s.st_mode):
                require(not installation or item.startswith(INSTALL + '/'), 'LINK_OUTSIDE_INSTALL')
                require((s.st_uid, s.st_gid) == (0, 0), 'LINK_OWNER')
                require(not FORBIDDEN.intersection(os.listxattr(item, follow_symlinks=False)), 'LINK_ATTRIBUTES')
                target = os.readlink(part, dir_fd=parent)
                old = self.links.setdefault(item, (snapshot(s), target))
                require(old == (snapshot(s), target), 'LINK_DRIFT')
                target = pp.normpath(pp.join(current, target))
                require(not installation or target.startswith(INSTALL + '/'), 'LINK_ESCAPE')
                count += 1
                require(count <= 40, 'LINK_BOUND')
                pending = collections.deque(target.strip('/').split('/') + list(pending))
                current = '/'
            else:
                require(stat.S_ISDIR(s.st_mode), 'PACKAGE_DIRECTORY_TYPE')
                self.open(item)
                current = item
        return current

    def read(self, path):
        fd = self.open(path, True)
        os.lseek(fd, 0, os.SEEK_SET)
        data = bounded_read(fd, 1048576)
        self.verify()
        os.lseek(fd, 0, os.SEEK_SET)
        require(hashlib.sha256(data).digest() == hashlib.sha256(bounded_read(fd, 1048576)).digest(), 'SOURCE_DIGEST_DRIFT')
        self.verify()
        return data

    def digest_runtime(self, path):
        fd = self.open(path, True)
        require(os.fstat(fd).st_size <= 256 * 1048576, 'RUNTIME_SIZE_BOUND')
        hashes, deadline = [], time.monotonic() + 30
        for _ in range(2):
            os.lseek(fd, 0, os.SEEK_SET)
            digest = hashlib.sha256()
            count = 0
            while chunk := os.read(fd, 1048576):
                count += len(chunk)
                require(count <= 256 * 1048576 and time.monotonic() <= deadline, 'RUNTIME_HASH_BOUND')
                digest.update(chunk)
            hashes.append(digest.hexdigest())
            self.verify()
        require(hashes[0] == hashes[1], 'RUNTIME_DIGEST_DRIFT')
        return hashes[0]

    def verify(self):
        for path, (fd, before, _) in self.held.items():
            require(snapshot(os.fstat(fd)) == before and snapshot(os.lstat(path)) == before, 'TRUST_METADATA_DRIFT')
        for path, before in self.links.items():
            require((snapshot(os.lstat(path)), os.readlink(path)) == before, 'TRUST_LINK_DRIFT')

    def close(self):
        for fd, _, _ in reversed(list(self.held.values())):
            os.close(fd)


def package_name(name):
    require(type(name) is str and re.fullmatch(r'(?:@[A-Za-z0-9_~.-]+/)?[A-Za-z0-9_~.-]+', name)
            and all(x not in {'.', '..'} for x in name.split('/')), 'PACKAGE_NAME')


def lookup_paths(anchor):
    current = pp.dirname(anchor)
    while current == INSTALL or current.startswith(INSTALL + '/'):
        if pp.basename(current) != 'node_modules':
            yield pp.join(current, 'node_modules')
        current = pp.dirname(current)


def unresolved_metadata(name, declaring_name, kind, digest):
    package_name(name)
    package_name(declaring_name)
    require(len(name) <= 214 and len(declaring_name) <= 214, 'DIAGNOSTIC_PACKAGE_NAME_BOUND')
    require(kind in {'dependencies', 'peerDependencies'}, 'DIAGNOSTIC_DEPENDENCY_KIND')
    require(type(digest) is str and re.fullmatch('[0-9a-f]{64}', digest), 'DIAGNOSTIC_MANIFEST_DIGEST')
    return {'unresolved_dependency': name, 'declaring_package': declaring_name,
            'dependency_kind': kind, 'declaring_manifest_sha256': digest}


def closure(trust, stats=None):
    started = time.monotonic()
    if stats is not None:
        stats.update(closure_package_count=0, closure_edge_count=0, closure_elapsed_ms=0,
                     unresolved_dependency=None, declaring_manifest_sha256=None,
                     declaring_package=None, dependency_kind=None)
    try:
        deadline = started + 30
        root_bytes = trust.read(PACKAGE + '/package.json')
        root = json.loads(root_bytes)
        links = {root['name']: PACKAGE}
        if stats is not None:
            stats['closure_package_count'] = len(links)
        canonicals = {root['name']: PACKAGE}
        queue = collections.deque([(PACKAGE + '/package.json', root, hashlib.sha256(root_bytes).hexdigest())])
        edges = 0
        while queue:
            anchor, manifest, manifest_digest = queue.popleft()
            for kind in ('dependencies', 'peerDependencies'):
                deps = manifest.get(kind, {})
                require(type(deps) is dict, 'DEPENDENCY_MAP')
                for name, version in deps.items():
                    edges += 1
                    if stats is not None:
                        stats['closure_edge_count'] = edges
                    require(edges <= 4096 and time.monotonic() <= deadline, 'CLOSURE_BOUND')
                    package_name(name)
                    require(type(version) is str, 'DEPENDENCY_VERSION')
                    if name in links:
                        continue
                    resolved = None
                    for search in lookup_paths(anchor):
                        logical = pp.join(search, name)
                        try:
                            canonical = trust.resolve(logical)
                        except FileNotFoundError:
                            continue
                        # An existing directory without its manifest is an invalid candidate.
                        data = trust.read(canonical + '/package.json')
                        child = json.loads(data)
                        require(type(child) is dict and child.get('name') == name and type(child.get('version')) is str,
                                'MANIFEST_IDENTITY')
                        require(name not in KNOWN_MAPPINGS or canonical == KNOWN_MAPPINGS[name]['canonical'],
                                'REVIEWED_PACKAGE_MAPPING')
                        resolved = logical, canonical, child, hashlib.sha256(data).hexdigest()
                        break
                    if resolved is None and stats is not None:
                        stats.update(unresolved_metadata(name, manifest.get('name'), kind, manifest_digest))
                    require(resolved is not None, 'INSTALLED_ONLY_RESOLUTION')
                    require(len(links) < 512, 'PACKAGE_BOUND')
                    logical, canonical, child, child_digest = resolved
                    links[name], canonicals[name] = logical, canonical
                    if stats is not None:
                        stats['closure_package_count'] = len(links)
                    queue.append((logical + '/package.json', child, child_digest))
        trust.verify()
        require(all(canonicals.get(name) == entry['canonical'] for name, entry in KNOWN_MAPPINGS.items()),
                'REVIEWED_CLOSURE_MAPPING')
        return links, canonicals
    finally:
        if stats is not None:
            stats['closure_elapsed_ms'] = max(0, int((time.monotonic() - started) * 1000))


def no_candidate_mounts():
    with open('/proc/self/mountinfo', encoding='ascii') as stream:
        for line in stream:
            target = line.split()[4]
            target = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), target)
            require(target != HOME and not target.startswith(HOME + '/'), 'CANDIDATE_MOUNT')


def candidate_inventory(links=None, canonical=None, trust=None):
    no_candidate_mounts()
    deadline, records, seen_links, seen = time.monotonic() + 30, [], set(), set()
    held = []
    root = None
    try:
        parent = None
        for part in ['/', 'home', 'dsh', '.dsh-profiles', 'vm105-provider-v1']:
            fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
            s = os.fstat(fd)
            held.append((fd, parent, part, snapshot(s)))
            require((s.st_uid, s.st_gid) == ((0, 0) if len(held) < 3 else (1000, 1000)), 'CANDIDATE_ANCESTOR_OWNER')
            require(not s.st_mode & 0o022 and not FORBIDDEN.intersection(os.listxattr(fd)), 'CANDIDATE_ANCESTOR_TRUST')
            if len(held) >= 4:
                require(stat.S_IMODE(s.st_mode) == 0o700, 'CANDIDATE_ANCESTOR_MODE')
            parent = fd
        root = parent
        device = os.fstat(root).st_dev
        expected_dirs = {'', 'profiles', 'profiles/web', 'spills'}
        link_dirs = {'profiles/node_modules'} | {'profiles/node_modules/' + n.split('/')[0] for n in (links or {}) if '/' in n}

        def visit(fd, relative, depth):
            require(depth <= 16 and time.monotonic() <= deadline, 'INVENTORY_BOUND')
            names = sorted(os.listdir(fd))
            for name in names:
                require(time.monotonic() <= deadline, 'INVENTORY_BOUND')
                path = relative + '/' + name if relative else name
                seen.add(path)
                require(len(seen) <= 4096, 'INVENTORY_BOUND')
                before = os.stat(name, dir_fd=fd, follow_symlinks=False)
                require(before.st_dev == device and (before.st_uid, before.st_gid) == (1000, 1000), 'CANDIDATE_OWNER_DEVICE')
                if stat.S_ISLNK(before.st_mode):
                    prefix = 'profiles/node_modules/'
                    key = path[len(prefix):] if path.startswith(prefix) else None
                    require(links is not None and key in links and before.st_nlink == 1, 'UNEXPECTED_CANDIDATE_LINK')
                    actual = os.readlink(name, dir_fd=fd)
                    full = HOME + '/' + path
                    require(not FORBIDDEN.intersection(os.listxattr(full, follow_symlinks=False)), 'CANDIDATE_LINK_ATTRIBUTES')
                    require(actual == links[key] and trust.resolve(actual) == canonical[key], 'FALLBACK_MAPPING')
                    require(snapshot(os.stat(name, dir_fd=fd, follow_symlinks=False)) == snapshot(before)
                            and os.readlink(name, dir_fd=fd) == actual, 'CANDIDATE_LINK_DRIFT')
                    seen_links.add(key)
                    kind = 'TRUSTED_INSTALLED_FALLBACK'
                else:
                    directory = stat.S_ISDIR(before.st_mode)
                    require(directory or stat.S_ISREG(before.st_mode), 'CANDIDATE_SPECIAL_FILE')
                    require(stat.S_IMODE(before.st_mode) == (0o700 if directory else 0o600), 'CANDIDATE_PRIVATE_MODE')
                    require(directory or before.st_nlink == 1, 'CANDIDATE_HARDLINK')
                    require(not path.startswith('profiles/node_modules/') or path in link_dirs, 'FALLBACK_EXTRA_ENTRY')
                    child = os.open(name, os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW |
                                    (os.O_DIRECTORY if directory else os.O_NONBLOCK), dir_fd=fd)
                    try:
                        require(snapshot(os.fstat(child)) == snapshot(before), 'CANDIDATE_OPEN_DRIFT')
                        require(not FORBIDDEN.intersection(os.listxattr(child)), 'CANDIDATE_ATTRIBUTES')
                        if directory:
                            visit(child, path, depth + 1)
                        elif path in FILES and (links is None or path != 'profiles/web/cordis.yml'):
                            data = bounded_read(child, 65536)
                            require(hashlib.sha256(data).hexdigest() == FILES[path], 'CANDIDATE_PIN')
                        require(snapshot(os.fstat(child)) == snapshot(before), 'CANDIDATE_READ_DRIFT')
                    finally:
                        os.close(child)
                    require(snapshot(os.stat(name, dir_fd=fd, follow_symlinks=False)) == snapshot(before), 'CANDIDATE_PATH_DRIFT')
                    kind = ('REVIEWED_INPUT' if path in FILES and path != 'profiles/web/cordis.yml' else
                            'EXPECTED_REWRITTEN_ROOT_METADATA' if path == 'profiles/web/cordis.yml' and links is not None else
                            'PRIVATE_UNCLASSIFIED_METADATA')
                records.append({'path': path, 'classification': kind, 'type': stat.S_IFMT(before.st_mode),
                                'uid': before.st_uid, 'gid': before.st_gid, 'mode': oct(stat.S_IMODE(before.st_mode)),
                                'size': before.st_size, 'device': before.st_dev, 'inode': before.st_ino})
            require(sorted(os.listdir(fd)) == names, 'CANDIDATE_DIRECTORY_DRIFT')

        visit(root, '', 0)
        require(set(FILES) <= seen, 'ORIGINAL_FILE_MISSING')
        if links is None:
            require(seen == (expected_dirs - {''}) | set(FILES), 'CANDIDATE_NOT_FRESH')
        else:
            require(seen_links == set(links) and link_dirs <= seen, 'FALLBACK_MISSING')
            trust.verify()
        no_candidate_mounts()
        for fd, parent, name, before in held:
            require(snapshot(os.fstat(fd)) == before and snapshot(os.stat(name, dir_fd=parent, follow_symlinks=False)) == before,
                    'CANDIDATE_ANCESTOR_DRIFT')
        return records
    finally:
        for fd, _, _, _ in reversed(held):
            os.close(fd)


def command(argv, timeout=10, input=None, fds=()):
    try:
        proc = subprocess.run(argv, input=input, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                              timeout=timeout, env={'PATH': '/usr/sbin:/usr/bin:/sbin:/bin', 'LC_ALL': 'C'},
                              pass_fds=fds, check=False)
    except subprocess.TimeoutExpired:
        raise Blocked('COMMAND_TIMEOUT') from None
    require(proc.returncode == 0 and len(proc.stdout) <= 1048576, 'COMMAND_FAILED')
    return proc.stdout.decode('utf-8')


def reject_envfile_directives(raw):
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    require('\r' not in text and '\0' not in text, 'UNIT_SOURCE_ENCODING')
    pending, section = '', None
    for line in text.splitlines():
        if line.lstrip().startswith(('#', ';')):
            continue
        line = pending + line
        if line.endswith('\\'):
            pending = line[:-1] + ' '
            continue
        pending = ''
        line = line.strip()
        if not line:
            continue
        require(not line.startswith('.include'), 'UNIT_SOURCE_INCLUDE')
        if re.fullmatch(r'\[(Unit|Service|Install)\]', line):
            section = line
            continue
        match = re.fullmatch(r'([A-Za-z][A-Za-z0-9]*)\s*=(.*)', line)
        require(section is not None and match is not None, 'UNIT_SOURCE_SYNTAX')
        require(match[1].lower() != 'environmentfile', 'UNIT_SOURCE_ENVIRONMENTFILE')
    require(not pending and section is not None, 'UNIT_SOURCE_INCOMPLETE')


def envfile_absence_proof(unit):
    require(unit in {PILOT, UNIT}, 'UNIT_SOURCE_TARGET')
    props = show(unit, ['FragmentPath', 'DropInPaths', 'PassEnvironment'])
    expected = '/etc/systemd/system/' + PILOT if unit == PILOT else '/run/systemd/transient/' + UNIT
    require(props == {'FragmentPath': expected, 'DropInPaths': '', 'PassEnvironment': ''}, 'UNIT_SOURCE_BOUNDARY')
    source = Trusted()
    try:
        reject_envfile_directives(source.read(expected))
        source.verify()
    finally:
        source.close()
    require(show(unit, ['FragmentPath', 'DropInPaths', 'PassEnvironment']) == props, 'UNIT_SOURCE_MAPPING_DRIFT')


def show(unit, keys):
    raw = command(['/usr/bin/systemctl', 'show', unit, '--all', '--no-pager', '--property=' + ','.join(keys)])
    values = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
    if set(keys) - set(values) == {'EnvironmentFiles'}:
        envfile_absence_proof(unit)
        values['EnvironmentFiles'] = ENV_SOURCE_PROOF
    require(set(values) == set(keys), 'UNIT_PROPERTIES_MISSING')
    return values


def effective_properties(unit):
    values = show(unit, list(EFFECTIVE) + ['EnvironmentFiles', 'InvocationID', 'Description', 'MainPID', 'ControlGroup', 'ActiveState'])
    require(all(values[k] == v for k, v in EFFECTIVE.items()) and values['EnvironmentFiles'] in {'', ENV_SOURCE_PROOF},
            'APPLIED_PROPERTIES')
    return values


def proc_read(pid, name, limit=65536):
    fd = os.open('/proc/' + str(pid) + '/' + name, os.O_RDONLY | os.O_CLOEXEC)
    try:
        return bounded_read(fd, limit)
    finally:
        os.close(fd)


def process(pid):
    raw = proc_read(pid, 'stat').decode()
    start = raw[raw.rfind(')') + 2:].split()[19]
    cgroup = proc_read(pid, 'cgroup').decode().strip()
    require(cgroup.startswith('0::/') and '\n' not in cgroup, 'CGROUP_V2_REQUIRED')
    return str(pid), start, cgroup[3:], os.readlink('/proc/' + str(pid) + '/ns/net')


def argv(pid):
    return [s.decode() for s in proc_read(pid, 'cmdline').rstrip(b'\0').split(b'\0')]


def environment(pid):
    result = {}
    for item in proc_read(pid, 'environ').rstrip(b'\0').split(b'\0'):
        key, value = item.split(b'=', 1)
        require(key.decode() not in result, 'DUPLICATE_ENVIRONMENT')
        result[key.decode()] = value.decode()
    return result


def listeners(pid):
    rows = []
    for table in ('tcp', 'tcp6'):
        for line in proc_read(pid, 'net/' + table).decode().splitlines()[1:]:
            parts = line.split()
            if parts[3] == '0A':
                rows.append((parts[1], parts[9]))
    return rows


def group_pids(group):
    require(re.fullmatch(r'/system.slice/deepseek-harness-candidate-smoke-20260909\.service', group), 'CGROUP_PATH')
    try:
        with open('/sys/fs/cgroup' + group + '/cgroup.procs', encoding='ascii') as stream:
            return set(int(x) for x in stream.read(65536).split())
    except FileNotFoundError:
        return set()


def socket_inodes(pid):
    result = set()
    for name in os.listdir('/proc/' + str(pid) + '/fd'):
        try:
            target = os.readlink('/proc/' + str(pid) + '/fd/' + name)
        except FileNotFoundError:
            continue
        match = re.fullmatch(r'socket:\[(\d+)\]', target)
        if match:
            result.add(match[1])
    return result


def net_shape(pid):
    dev = proc_read(pid, 'net/dev').decode().splitlines()[2:]
    require({line.split(':')[0].strip() for line in dev} == {'lo'}, 'NETWORK_INTERFACES')
    for line in proc_read(pid, 'net/route').decode().splitlines()[1:]:
        cells = line.split()
        require(cells[0] == 'lo' and cells[1] != '00000000' and cells[2] == '00000000', 'NETWORK_ROUTES')
    for line in proc_read(pid, 'net/ipv6_route').decode().splitlines():
        cells = line.split()
        # Reject actual default routes; kernel's unreachable placeholder is not a route out.
        reject = bool(int(cells[8], 16) & 0x200)
        require(cells[-1] == 'lo' and (cells[0] != '0' * 32 or cells[1] != '00' or reject), 'NETWORK_IPV6_ROUTES')


def pilot_baseline():
    keys = ['ActiveState', 'MainPID', 'ExecMainStartTimestampMonotonic', 'NRestarts', 'Environment',
            'EnvironmentFiles', 'PassEnvironment', 'DropInPaths', 'User', 'Group', 'WorkingDirectory', 'UMask']
    p = show(PILOT, keys)
    require(p['ActiveState'] == 'active' and p['MainPID'].isdigit() and int(p['MainPID']) > 1, 'PILOT_NOT_ACTIVE')
    require(p['EnvironmentFiles'] in {'', ENV_SOURCE_PROOF} and p['PassEnvironment'] == p['DropInPaths'] == '',
            'PILOT_ENVIRONMENT_SOURCE')
    require((p['User'], p['Group'], p['WorkingDirectory'], p['UMask']) == ('dsh', 'dsh', '/srv/dsh/workspaces', '0077'),
            'PILOT_PROPERTIES')
    pairs = [v.split('=', 1) for v in shlex.split(p['Environment'])]
    env = dict(pairs)
    require(len(pairs) == 3 and set(env) == {'HOME', 'DSH_HOME', 'PATH'} and env['HOME'] == '/home/dsh'
            and env['DSH_HOME'] == OLD, 'PILOT_ENVIRONMENT')
    require(all(x.startswith('/') and pp.normpath(x) == x for x in env['PATH'].split(':')), 'PILOT_PATH')
    identity = process(p['MainPID'])
    args = argv(p['MainPID'])
    require(args[-5:] == ['web', '--host', '127.0.0.1', '--port', '3080'], 'PILOT_ARGV')
    p.pop('Environment')
    return p, identity, args, env['PATH']


PROBE = r'''
import json, signal, sys, urllib.request
assert sys.flags.optimize == 0
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None
def expired(*unused): raise TimeoutError()
signal.signal(signal.SIGALRM, expired)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
def request(method=None, rpc_id=None):
    url = 'http://127.0.0.1:3081/'
    body = None
    if method:
        assert method in ('llm.providers', 'host.describe')
        url += 'api/' + method
        body = json.dumps({'type':'client-request','rpcId':rpc_id,'method':method,'payload':{}}).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type':'application/json'})
    signal.alarm(5)
    try:
        with opener.open(req, timeout=5) as response:
            assert response.status == 200
            raw = response.read(65537)
            assert len(raw) <= 65536
        if not method: return None
        env = json.loads(raw)
        assert type(env) is dict and env.get('type') == 'server-response' and env.get('rpcId') == rpc_id
        result = env.get('result')
        assert type(result) is dict and result.get('ok') is True and type(result.get('value')) is dict
        return result['value']
    finally: signal.alarm(0)
try:
    request()
    rows = request('llm.providers', 'vm105-cutover-route-count').get('providers')
    assert type(rows) is list and all(type(r) is dict and type(r.get('active')) is bool for r in rows)
    count = sum(r['active'] for r in rows)
    assert count == 0
    default = request('host.describe', 'vm105-cutover-default-check')
    assert default.get('provider') == 'deepseek-official' and default.get('model') == 'deepseek-v4-flash'
    print(json.dumps({'status':'PASS','registered_route_count':count,'native_default_matches':True}))
except Exception:
    print(json.dumps({'status':'API_PROBE_BLOCKED'})); sys.exit(1)
'''


def apply():
    require(sys.platform == 'linux' and sys.version_info[:2] == (3, 12) and sys.flags.optimize == 0,
            'PYTHON_RUNTIME')
    require(os.geteuid() == 0 and os.getegid() == 0, 'ROOT_REQUIRED')
    require(socket.gethostname() == 'deepseek-harness-01', 'HOST_IDENTITY')
    trust, owner, group, netfd, started = Trusted(), None, None, None, False
    observed_processes = {}
    result = {'status': 'BLOCKED', 'runtime': 'NOT PROVEN', 'checkpoints': []}
    before = None
    description = 'vm105-candidate-smoke-owned-' + uuid.uuid4().hex
    try:
        require(SOURCE_PINS, 'SOURCE_PINS_MISSING')
        for path, digest in SOURCE_PINS.items():
            require(hashlib.sha256(trust.read(path)).hexdigest() == digest, 'SOURCE_PIN')
        for path in ('/usr/bin/python3.12', '/usr/bin/nsenter', '/usr/bin/systemd-run', '/usr/bin/systemctl', '/usr/bin/env'):
            fd = trust.open(path, True)
            require(os.fstat(fd).st_mode & 0o111, 'TOOL_EXECUTABLE')
        for name, entry in KNOWN_MAPPINGS.items():
            require(trust.resolve(entry['logical']) == entry['canonical'], 'REVIEWED_LOGICAL_MAPPING')
        # Read the reviewed root-owned wrapper as data and bind its only exec to the pinned CLI.
        launch = '/usr/local/bin/dsh'
        launch_bytes = trust.read(launch)
        s = os.lstat(launch)
        require(s.st_nlink == 1 and s.st_mode & 0o111, 'LAUNCHER_METADATA')
        launch_lines = launch_bytes.decode('utf-8').splitlines()
        require(launch_lines and launch_lines[0] in {'#!/bin/sh', '#!/bin/bash', '#!/usr/bin/bash'}, 'LAUNCHER_SHEBANG')
        meaningful = [line for line in launch_lines[1:] if line and line not in {'set -e', 'set -eu'}]
        require(len(meaningful) == 1, 'LAUNCHER_SHAPE')
        match = re.fullmatch(r'exec (/opt/node-v24\.19\.0-linux-x64/bin/node) (/opt/deepseek-harness/[A-Za-z0-9._/@+-]+) "\$@"', meaningful[0])
        require(match is not None, 'LAUNCHER_FIXED_EXEC')
        canonical_entry = trust.resolve(pp.dirname(match[2])) + '/' + pp.basename(match[2])
        require(canonical_entry == PACKAGE + '/lib/bin.js', 'LAUNCHER_REVIEWED_ENTRY')
        require(trust.digest_runtime(match[1]) == 'bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12',
                'NODE_RUNTIME_PIN')
        require(os.stat(match[1]).st_mode & 0o111, 'NODE_EXECUTABLE')
        before = pilot_baseline()
        baseline, pilot, pilot_args, path = before
        require(pilot_args[:-5] == [match[1], match[2]], 'PILOT_REVIEWED_ENTRY')
        if baseline['EnvironmentFiles'] == ENV_SOURCE_PROOF:
            result['checkpoints'].append('PILOT_ENVIRONMENTFILES_ABSENT_SOURCE_VERIFIED')
        for component in path.split(':'):
            trust.resolve(component, installation=False)
        require(not any(row[0].endswith(':0C09') for row in listeners('self')), 'HOST_3081_EXISTS')
        require(pilot[3] == os.readlink('/proc/self/ns/net'), 'PILOT_NAMESPACE')
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')
        candidate_inventory()
        links, canonicals = closure(trust)
        require(show(UNIT, ['LoadState'])['LoadState'] == 'not-found', 'UNIT_ALREADY_EXISTS')
        candidate_inventory()
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')
        result['checkpoints'].append('PREFLIGHT_PASS')
        trust.verify()
        launch_before = snapshot(os.lstat(launch))
        require(launch_before == snapshot(s), 'LAUNCHER_DRIFT')
        args = ['/usr/bin/systemd-run', '--unit=' + UNIT, '--description=' + description, '--quiet', '--no-block']
        args += ['--property=' + k + '=' + v for k, v in PROPERTIES.items()]
        args += ['--', '/usr/bin/env', '-i', 'HOME=/home/dsh', 'DSH_HOME=' + HOME, 'PATH=' + path,
                 launch, 'web', '--host', '127.0.0.1', '--port', '3081', '--no-open']
        started = True
        command(args, 10)
        deadline = time.monotonic() + 30
        listener_pid, identity = None, None
        while time.monotonic() < deadline:
            unit = effective_properties(UNIT)
            require(unit['Description'] == description and re.fullmatch('[0-9a-f]{32}', unit['InvocationID']), 'UNIT_OWNERSHIP')
            owner = unit['InvocationID'], description
            group = unit['ControlGroup']
            require(unit['ActiveState'] in {'active', 'activating'}, 'CANDIDATE_TERMINATED')
            pids = group_pids(group)
            for pid in pids:
                current = process(pid)
                observed_processes[pid] = current
                require(current[2] == group and current[3] != pilot[3], 'CANDIDATE_NAMESPACE_CGROUP')
                if netfd is None:
                    netfd = os.open('/proc/' + str(pid) + '/ns/net', os.O_RDONLY | os.O_CLOEXEC)
                require(os.readlink('/proc/self/fd/' + str(netfd)) == current[3], 'NAMESPACE_FD_IDENTITY')
                rows = listeners(pid)
                if rows and any(inode in socket_inodes(pid) for _, inode in rows):
                    validate_listener(rows, socket_inodes(pid))
                    require(listener_pid is None, 'MULTIPLE_LISTENER_OWNERS')
                    listener_pid, identity = pid, current
            if listener_pid is not None:
                break
            time.sleep(0.25)
        require(identity is not None, 'LISTENER_TIMEOUT')
        require(os.readlink('/proc/self/fd/' + str(netfd)) == identity[3], 'NAMESPACE_FD_IDENTITY')
        time.sleep(5)
        require(process(listener_pid) == identity and listener_pid in group_pids(group), 'PROCESS_IDENTITY_DRIFT')
        status = dict(line.split(':', 1) for line in proc_read(listener_pid, 'status').decode().splitlines() if ':' in line)
        require(status['Uid'].split() == ['1000'] * 4 and status['Gid'].split() == ['1000'] * 4, 'LISTENER_UID_GID')
        validate_selector(environment(listener_pid), path)
        require(argv(listener_pid) == pilot_args[:-5] + ['web', '--host', '127.0.0.1', '--port', '3081', '--no-open'],
                'CANDIDATE_ARGV')
        validate_listener(listeners(listener_pid), socket_inodes(listener_pid))
        net_shape(listener_pid)
        require(not any(row[0].endswith(':0C09') for row in listeners('self')), 'HOST_LISTENER_CREATED')
        preprobe = effective_properties(UNIT)
        validate_owned(preprobe, owner)
        require(preprobe['ControlGroup'] == group
                and preprobe['ActiveState'] == 'active', 'PREPROBE_UNIT_DRIFT')
        if preprobe['EnvironmentFiles'] == ENV_SOURCE_PROOF:
            result['checkpoints'].append('CANDIDATE_ENVIRONMENTFILES_ABSENT_SOURCE_VERIFIED')
        require(process(listener_pid) == identity, 'PREPROBE_IDENTITY_DRIFT')
        result['checkpoints'].append('ISOLATION_PASS')
        raw = command(['/usr/bin/nsenter', '--net=/proc/self/fd/' + str(netfd), '/usr/bin/python3.12', '-I', '-c', PROBE],
                      18, fds=(netfd,))
        require(json.loads(raw) == {'status': 'PASS', 'registered_route_count': 0, 'native_default_matches': True}, 'API_RECEIPT')
        result['checkpoints'].append('API_READBACK_PASS')
        result.update({'registered_route_count': 0, 'native_default_matches': True, 'status': 'PROBE_PASS_CLEANUP_PENDING'})
    except Blocked as error:
        result['error_code'] = str(error)
    except Exception:
        result['error_code'] = 'UNEXPECTED_FAILURE'
    finally:
        if started:
            try:
                props = show(UNIT, ['InvocationID', 'Description', 'Transient', 'ControlGroup'])
                if owner is None:
                    require(props['Description'] == description and props['Transient'] == 'yes'
                            and re.fullmatch('[0-9a-f]{32}', props['InvocationID']), 'CLEANUP_OWNERSHIP')
                    owner = props['InvocationID'], description
                    group = props['ControlGroup']
                validate_owned(props, owner)
                command(['/usr/bin/systemctl', 'stop', UNIT], 30)
                state = show(UNIT, ['LoadState', 'ActiveState'])
                require(state['ActiveState'] in {'inactive', 'failed'} or state['LoadState'] == 'not-found', 'UNIT_NOT_STOPPED')
                require(not group_pids(group), 'CGROUP_NOT_EMPTY')
                for pid, prior in observed_processes.items():
                    try:
                        remaining = process(pid)
                    except (FileNotFoundError, ProcessLookupError):
                        continue
                    require(remaining[1] != prior[1], 'CANDIDATE_PROCESS_REMAINS')
                require(netfd is not None, 'HELD_NAMESPACE_UNAVAILABLE')
                check = "import pathlib,sys;sys.exit(any(l.split()[3]=='0A' and l.split()[1].endswith(':0C09') for n in ('tcp','tcp6') for l in pathlib.Path('/proc/self/net/'+n).read_text().splitlines()[1:]))"
                command(['/usr/bin/nsenter', '--net=/proc/self/fd/' + str(netfd), '/usr/bin/python3.12', '-I', '-c', check],
                        5, fds=(netfd,))
                result['checkpoints'].append('OWNED_CLEANUP_PASS')
                if result['status'] == 'PROBE_PASS_CLEANUP_PENDING':
                    result['inventory'] = candidate_inventory(links, canonicals, trust)
                    result['checkpoints'].append('CONTAINMENT_METADATA_PASS')
                    result['status'] = 'ISOLATED_CANDIDATE_SMOKE_PASS'
                    result['runtime'] = 'ISOLATED_CONTAINMENT_ONLY'
            except Blocked as error:
                result.update(status='CLEANUP_NOT_PROVEN' if 'OWNED_CLEANUP_PASS' not in result['checkpoints'] else 'BLOCKED',
                              error_code=str(error))
            except Exception:
                result.update(status='CLEANUP_NOT_PROVEN' if 'OWNED_CLEANUP_PASS' not in result['checkpoints'] else 'BLOCKED',
                              error_code='CLEANUP_OR_INVENTORY_FAILURE')
        if before is not None:
            try:
                require(pilot_baseline() == before, 'PILOT_CHANGED')
                result['checkpoints'].append('PILOT_IDENTITY_UNCHANGED')
            except Exception:
                result.update(status='BLOCKED' if result['status'] != 'CLEANUP_NOT_PROVEN' else result['status'],
                              pilot_error_code='PILOT_PRESERVATION_NOT_PROVEN')
        if netfd is not None:
            os.close(netfd)
        trust.close()
    result['parent_http_and_tunnel_verification'] = 'REQUIRED_SEPARATELY'
    return result


DIAGNOSTIC_CODES = frozenset({
    'CLOSURE_BOUND', 'PACKAGE_BOUND', 'PACKAGE_NAME', 'DEPENDENCY_MAP', 'DEPENDENCY_VERSION',
    'MANIFEST_IDENTITY', 'REVIEWED_PACKAGE_MAPPING', 'REVIEWED_CLOSURE_MAPPING', 'INSTALLED_ONLY_RESOLUTION',
    'TRUST_PATH', 'TRUST_OWNER_MODE', 'TRUST_TYPE', 'TRUST_LINK_COUNT', 'TRUST_ATTRIBUTES',
    'TRUST_METADATA_DRIFT', 'TRUST_LINK_DRIFT', 'INSTALL_ESCAPE', 'LINK_OUTSIDE_INSTALL', 'LINK_OWNER',
    'LINK_ATTRIBUTES', 'LINK_DRIFT', 'LINK_ESCAPE', 'LINK_BOUND', 'PACKAGE_DIRECTORY_TYPE',
    'READ_BOUND', 'SOURCE_DIGEST_DRIFT', 'SOURCE_PIN', 'SOURCE_PINS_MISSING',
    'DIAGNOSTIC_FD_HARD_LIMIT', 'DIAGNOSTIC_FD_LIMIT_MISMATCH', 'DIAGNOSTIC_FD_RESTORE_MISMATCH',
    'DIAGNOSTIC_PACKAGE_NAME_BOUND',
    'DIAGNOSTIC_DEPENDENCY_KIND', 'DIAGNOSTIC_MANIFEST_DIGEST',
})


def diagnostic_error(error):
    names = {'Blocked', 'TimeoutError', 'OSError', 'FileNotFoundError', 'PermissionError',
             'ProcessLookupError', 'NotADirectoryError', 'IsADirectoryError', 'JSONDecodeError',
             'UnicodeDecodeError', 'ValueError', 'KeyError', 'IndexError', 'TypeError'}
    name = type(error).__name__
    number = getattr(error, 'errno', None)
    code = None
    if type(error) is Blocked:
        code = error.args[0] if len(error.args) == 1 and type(error.args[0]) is str else None
        code = code if code in DIAGNOSTIC_CODES else 'UNCLASSIFIED_BLOCKED'
    return {'exception_class': name if name in names else 'OTHER',
            'errno': number if type(number) is int else None, 'safe_code': code}


def preflight_diagnostic():
    """Read-only reproduction: this entry has no path to apply or unit controls."""
    result = {'status': 'DIAGNOSTIC_BLOCKED', 'stage': 'RUNTIME', 'exception_class': None, 'errno': None, 'safe_code': None,
              'closure_package_count': None, 'closure_edge_count': None, 'closure_elapsed_ms': None,
              'unresolved_dependency': None, 'declaring_manifest_sha256': None,
              'declaring_package': None, 'dependency_kind': None,
              'held_fd_count': 0, 'last_successful_fd_count': None, 'fd_soft_limit': None, 'fd_hard_limit': None,
              'fd_applied_soft_limit': None, 'fd_applied_hard_limit': None,
              'fd_restored_soft_limit': None, 'fd_restored_hard_limit': None,
              'fd_restoration': 'NOT_ATTEMPTED'}
    trust, previous_handler, original_limits, limit_attempted = Trusted(), None, None, False

    def stage(name):
        result['stage'] = name
        try:
            result['last_successful_fd_count'] = len(os.listdir('/proc/self/fd'))
        except OSError:
            pass  # Keep the last successful observation; do not adapt limits to observed usage.

    def deadline(*unused):
        raise TimeoutError()

    try:
        require(sys.platform == 'linux' and sys.version_info[:2] == (3, 12) and sys.flags.optimize == 0,
                'PYTHON_RUNTIME')
        require(os.geteuid() == 0 and os.getegid() == 0 and socket.gethostname() == 'deepseek-harness-01',
                'DIAGNOSTIC_IDENTITY')
        import resource
        original_limits = resource.getrlimit(resource.RLIMIT_NOFILE)
        result['fd_soft_limit'], result['fd_hard_limit'] = original_limits
        previous_handler = signal.signal(signal.SIGALRM, deadline)
        signal.alarm(60)
        stage('FD_LIMIT_CONFIG')
        require(original_limits[1] >= 4096, 'DIAGNOSTIC_FD_HARD_LIMIT')
        limit_attempted = True
        resource.setrlimit(resource.RLIMIT_NOFILE, (4096, original_limits[1]))
        applied = resource.getrlimit(resource.RLIMIT_NOFILE)
        result['fd_applied_soft_limit'], result['fd_applied_hard_limit'] = applied
        require(applied == (4096, original_limits[1]), 'DIAGNOSTIC_FD_LIMIT_MISMATCH')
        stage('SOURCE_PINS')
        require(SOURCE_PINS, 'SOURCE_PINS_MISSING')
        for path, digest in SOURCE_PINS.items():
            require(hashlib.sha256(trust.read(path)).hexdigest() == digest, 'SOURCE_PIN')
        stage('TOOLS')
        for path in ('/usr/bin/python3.12', '/usr/bin/nsenter', '/usr/bin/systemd-run', '/usr/bin/systemctl', '/usr/bin/env'):
            require(os.fstat(trust.open(path, True)).st_mode & 0o111, 'TOOL_EXECUTABLE')
        stage('PACKAGE_MAPPINGS')
        for entry in KNOWN_MAPPINGS.values():
            require(trust.resolve(entry['logical']) == entry['canonical'], 'REVIEWED_LOGICAL_MAPPING')
        stage('LAUNCHER')
        launch = '/usr/local/bin/dsh'
        launch_lines = trust.read(launch).decode('utf-8').splitlines()
        metadata = os.lstat(launch)
        require(metadata.st_nlink == 1 and metadata.st_mode & 0o111, 'LAUNCHER_METADATA')
        require(launch_lines and launch_lines[0] in {'#!/bin/sh', '#!/bin/bash', '#!/usr/bin/bash'}, 'LAUNCHER_SHEBANG')
        meaningful = [line for line in launch_lines[1:] if line and line not in {'set -e', 'set -eu'}]
        require(len(meaningful) == 1, 'LAUNCHER_SHAPE')
        match = re.fullmatch(r'exec (/opt/node-v24\.19\.0-linux-x64/bin/node) (/opt/deepseek-harness/[A-Za-z0-9._/@+-]+) "\$@"', meaningful[0])
        require(match is not None, 'LAUNCHER_FIXED_EXEC')
        require(trust.resolve(pp.dirname(match[2])) + '/' + pp.basename(match[2]) == PACKAGE + '/lib/bin.js',
                'LAUNCHER_REVIEWED_ENTRY')
        require(trust.digest_runtime(match[1]) == 'bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12',
                'NODE_RUNTIME_PIN')
        require(os.stat(match[1]).st_mode & 0o111, 'NODE_EXECUTABLE')
        stage('PILOT_BASELINE')
        baseline, pilot, pilot_args, path = pilot_baseline()
        require(pilot_args[:-5] == [match[1], match[2]], 'PILOT_REVIEWED_ENTRY')
        stage('PATH_METADATA')
        for component in path.split(':'):
            trust.resolve(component, installation=False)
        stage('HOST_LISTENER')
        require(not any(row[0].endswith(':0C09') for row in listeners('self')), 'HOST_3081_EXISTS')
        require(pilot[3] == os.readlink('/proc/self/ns/net'), 'PILOT_NAMESPACE')
        stage('WORKSPACE_ENV_ABSENCE')
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')
        stage('CANDIDATE_INVENTORY')
        candidate_inventory()
        stage('INSTALLED_CLOSURE')
        closure(trust, result)
        stage('UNIT_ABSENCE')
        require(show(UNIT, ['LoadState'])['LoadState'] == 'not-found', 'UNIT_ALREADY_EXISTS')
        stage('FINAL_CANDIDATE_INVENTORY')
        candidate_inventory()
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')
        stage('FINAL_HELD_METADATA')
        trust.verify()
        result['status'] = 'READ_ONLY_PREFLIGHT_PASS'
    except Exception as error:
        result.update(diagnostic_error(error))
    finally:
        result['held_fd_count'] = len(trust.held)
        # Every retained descriptor belongs to this instance. Continue closing even after one error.
        for fd, _, _ in reversed(list(trust.held.values())):
            try:
                os.close(fd)
            except Exception as error:
                if result['exception_class'] is None:
                    result.update(diagnostic_error(error))
                result['status'] = 'DIAGNOSTIC_BLOCKED'
        if limit_attempted:
            result['fd_restoration'] = 'PASS'
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, original_limits)
            except Exception as error:
                result['fd_restoration'] = 'FAILED'
                result['restoration_error'] = diagnostic_error(error)
            try:
                restored = resource.getrlimit(resource.RLIMIT_NOFILE)
                result['fd_restored_soft_limit'], result['fd_restored_hard_limit'] = restored
                require(restored == original_limits, 'DIAGNOSTIC_FD_RESTORE_MISMATCH')
            except Exception as error:
                result['fd_restoration'] = 'FAILED'
                result.setdefault('restoration_error', diagnostic_error(error))
            if result['fd_restoration'] == 'FAILED':
                result['status'] = 'FD_LIMIT_RESTORE_FAILED'
        if previous_handler is not None:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
    return result


def self_test():
    import contextlib
    import io
    import urllib.request
    from types import SimpleNamespace
    from unittest.mock import patch
    good = {'DSH_HOME': HOME, 'HOME': '/home/dsh', 'PATH': '/usr/bin'}
    validate_selector(good, '/usr/bin')
    validate_listener([('0100007F:0C09', '77')], {'77'})
    validate_owned({'InvocationID': 'a', 'Description': 'b'}, ('a', 'b'))
    require(diagnostic_error(OSError(24, 'must never appear in output')) == {'exception_class': 'OSError', 'errno': 24, 'safe_code': None},
            'SELF_TEST_DIAGNOSTIC_SANITIZATION')
    require(diagnostic_error(Blocked('PACKAGE_BOUND'))['safe_code'] == 'PACKAGE_BOUND'
            and diagnostic_error(Blocked('must never appear in output'))['safe_code'] == 'UNCLASSIFIED_BLOCKED'
            and diagnostic_error(Blocked('PACKAGE_BOUND', 'arbitrary extra text'))['safe_code'] == 'UNCLASSIFIED_BLOCKED'
            and diagnostic_error(ValueError('PACKAGE_BOUND'))['safe_code'] is None, 'SELF_TEST_DIAGNOSTIC_CODE_ALLOWLIST')
    root_manifest = {'name': '@deepseek-ai/dsh', 'dependencies': {f'p{i}': '*' for i in range(512)}}
    mock_closure = SimpleNamespace(
        read=lambda path: json.dumps(root_manifest if path == PACKAGE + '/package.json' else
                                     {'name': pp.basename(pp.dirname(path)), 'version': '1'}).encode(),
        resolve=lambda path: INSTALL + '/mock/' + pp.basename(path), verify=lambda: None)
    counters = {}
    with patch.dict(globals(), {'KNOWN_MAPPINGS': {}}):
        try:
            closure(mock_closure, counters)
        except Blocked as error:
            require(error.args == ('PACKAGE_BOUND',), 'SELF_TEST_CLOSURE_GUARD')
        else:
            raise RuntimeError('package bound accepted')
    require(counters['closure_package_count'] == 512 and counters['closure_edge_count'] == 512
            and type(counters['closure_elapsed_ms']) is int and counters['closure_elapsed_ms'] >= 0,
            'SELF_TEST_CLOSURE_METRICS')
    declaring_bytes = b'{ "name": "@deepseek-ai/dsh", "dependencies": { "@fixture/missing": "*" } }\n'
    def missing_package(*unused):
        raise FileNotFoundError()
    unresolved = SimpleNamespace(read=lambda _: declaring_bytes, resolve=missing_package, verify=lambda: None)
    counters = {}
    try:
        closure(unresolved, counters)
    except Blocked as error:
        require(error.args == ('INSTALLED_ONLY_RESOLUTION',), 'SELF_TEST_UNRESOLVED_GUARD')
    else:
        raise RuntimeError('unresolved package accepted')
    require(counters['unresolved_dependency'] == '@fixture/missing'
            and counters['declaring_package'] == '@deepseek-ai/dsh' and counters['dependency_kind'] == 'dependencies'
            and counters['declaring_manifest_sha256'] == hashlib.sha256(declaring_bytes).hexdigest()
            and counters['declaring_manifest_sha256'] != hashlib.sha256(json.dumps(json.loads(declaring_bytes)).encode()).hexdigest(),
            'SELF_TEST_EXACT_DECLARING_BYTES')
    def exhausted(*unused):
        raise OSError(24, 'must never appear in output')
    fake = SimpleNamespace(held={'mock': (71, None, None)}, read=exhausted)
    for fail_restore in (False, True):
        limits, events = [1024, 1048576], []
        def set_limits(unused, values):
            events.append(('set', values))
            require(values[1] == 1048576, 'SELF_TEST_HARD_LIMIT_CHANGED')
            if fail_restore and values[0] == 1024:
                raise PermissionError(1, 'must never appear in output')
            limits[:] = values
        with patch.dict(globals(), {'Trusted': lambda: fake}), \
             patch.dict(sys.modules, {'resource': SimpleNamespace(RLIMIT_NOFILE=7, getrlimit=lambda _: tuple(limits), setrlimit=set_limits)}), \
             patch.object(sys, 'platform', 'linux'), patch.object(socket, 'gethostname', return_value='deepseek-harness-01'), \
             patch.object(os, 'geteuid', return_value=0, create=True), patch.object(os, 'getegid', return_value=0, create=True), \
             patch.object(os, 'listdir', return_value=['one', 'two']), \
             patch.object(os, 'close', side_effect=lambda fd: events.append(('close', fd))), \
             patch.object(signal, 'signal'), patch.object(signal, 'alarm', create=True), patch.object(signal, 'SIGALRM', 14, create=True):
            diagnostic = preflight_diagnostic()
        require(diagnostic['status'] == ('FD_LIMIT_RESTORE_FAILED' if fail_restore else 'DIAGNOSTIC_BLOCKED')
                and diagnostic['stage'] == 'SOURCE_PINS' and diagnostic['errno'] == 24
                and diagnostic['held_fd_count'] == 1 and diagnostic['last_successful_fd_count'] == 2,
                'SELF_TEST_DIAGNOSTIC_FAILURE')
        require(events == [('set', (4096, 1048576)), ('close', 71), ('set', (1024, 1048576))],
                'SELF_TEST_LIMIT_RESTORE_ORDER')
        require(diagnostic['fd_applied_hard_limit'] == diagnostic['fd_restored_hard_limit'] == 1048576
                and diagnostic['fd_restored_soft_limit'] == (4096 if fail_restore else 1024)
                and diagnostic['fd_restoration'] == ('FAILED' if fail_restore else 'PASS'), 'SELF_TEST_LIMIT_RESTORATION')
    reject_envfile_directives(b'\xef\xbb\xbf[Service]\r\n# Comment\r\nExecStart=/usr/bin/env \\\r\n -i /bin/true\r\n')
    cases = [
        lambda: validate_selector({'HOME': '/home/dsh', 'PATH': '/usr/bin'}, '/usr/bin'),
        lambda: validate_listener([('0100007F:0C09', '77')], {'78'}),
        lambda: validate_owned({'InvocationID': 'wrong', 'Description': 'b'}, ('a', 'b')),
        lambda: reject_envfile_directives(b'[Service]\nEnvironmentFile=\n'),
        lambda: reject_envfile_directives(b'[Service]\nEnvironmentFile=\\\n /secret\n'),
        lambda: reject_envfile_directives(b'.include /another-unit\n'),
        lambda: reject_envfile_directives(b'[Service]\ninvalid syntax\n'),
        lambda: unresolved_metadata('dependency', '../../invalid', 'dependencies', '0' * 64),
        lambda: unresolved_metadata('dependency', 'a' * 215, 'dependencies', '0' * 64),
        lambda: unresolved_metadata('dependency', 'declaring', 'optionalDependencies', '0' * 64),
    ]
    for case in cases:
        try:
            case()
        except Blocked:
            continue
        raise RuntimeError('rejection test accepted')
    # Exercise the exact subprocess probe with a mocked opener, including both API rejects.
    class Response(io.BytesIO):
        status = 200
    for active, provider, expected in [(False, 'deepseek-official', 'PASS'),
                                       (True, 'deepseek-official', 'API_PROBE_BLOCKED'),
                                       (False, 'wrong', 'API_PROBE_BLOCKED')]:
        class Opener:
            def open(self, req, timeout):
                if req.data is None:
                    return Response(b'root')
                body = json.loads(req.data)
                value = ({'providers': [{'active': active}]} if body['method'] == 'llm.providers' else
                         {'provider': provider, 'model': 'deepseek-v4-flash'})
                return Response(json.dumps({'type': 'server-response', 'rpcId': body['rpcId'],
                                            'result': {'ok': True, 'value': value}}).encode())
        out = io.StringIO()
        with patch.object(urllib.request, 'build_opener', return_value=Opener()), \
             patch.object(signal, 'signal'), patch.object(signal, 'alarm', create=True), contextlib.redirect_stdout(out):
            # Windows lacks SIGALRM; this mock-only symbol is never used by --apply.
            with patch.object(signal, 'SIGALRM', 14, create=True):
                try:
                    exec(PROBE, {})
                except SystemExit as error:
                    require(error.code == 1 and expected != 'PASS', 'SELF_TEST_EXIT')
        require(json.loads(out.getvalue())['status'] == expected, 'SELF_TEST_API_RESULT')
    return {'status': 'SELF_TEST_PASS', 'rejection_cases': len(cases) + 2}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--apply', action='store_true')
    modes.add_argument('--self-test', action='store_true')
    modes.add_argument('--preflight-diagnostic', action='store_true')
    args = parser.parse_args()
    try:
        result = self_test() if args.self_test else preflight_diagnostic() if args.preflight_diagnostic else apply() if args.apply else {
            'status': 'CONTRACT_ONLY', 'runtime': 'NOT PROVEN', 'unit': UNIT,
            'candidate': HOME, 'properties': PROPERTIES, 'attempts': 1,
            'required_parent_checks': ['fresh source receipts', 'pilot loopback HTTP before/after', 'tunnel before/after'],
        }
    except Exception:
        result = {'status': 'BLOCKED', 'error_code': 'PRECONDITION_OR_SELF_TEST_FAILURE'}
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result['status'] in {'CONTRACT_ONLY', 'SELF_TEST_PASS', 'ISOLATED_CANDIDATE_SMOKE_PASS', 'READ_ONLY_PREFLIGHT_PASS'} else 1)
