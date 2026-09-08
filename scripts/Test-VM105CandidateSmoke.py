#!/usr/bin/env python3
"""One isolated candidate attempt. Default prints contract; --apply is explicit."""
import argparse
import collections
import hashlib
import json
import os
import posixpath as pp
import re
import selectors
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
UNIT_V2 = 'deepseek-harness-candidate-smoke-20260909-v2.service'
UNIT_V3 = 'deepseek-harness-candidate-smoke-20260909-v3.service'
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
                  'PassEnvironment': '', 'JoinsNamespaceOf': '', 'Sockets': '', 'TriggeredBy': ''})
ENV_SOURCE_PROOF = 'ABSENT_SOURCE_VERIFIED'
SOCKET_SOURCE_PROOF = 'SOCKETS_ABSENT_SOURCE_VERIFIED'
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


def census_context(anchor, manifest, digest, kind):
    resolver_path(anchor)
    require(anchor.startswith(INSTALL + '/') and pp.basename(anchor) == 'package.json', 'RESOLVER_ANCHOR')
    name = manifest.get('name')
    package_name(name)
    require(len(name) <= 214, 'DIAGNOSTIC_PACKAGE_NAME_BOUND')
    return {'declaring_package': name, 'declaring_manifest_sha256': digest,
            'logical_anchor': anchor, 'dependency_kind': kind}


def optional_classification(manifest, name, kind):
    if kind != 'peerDependencies' or 'peerDependenciesMeta' not in manifest:
        return 'MISSING'
    metadata = manifest['peerDependenciesMeta']
    if type(metadata) is not dict:
        return 'MALFORMED'
    if name not in metadata:
        return 'MISSING'
    row = metadata[name]
    if type(row) is not dict:
        return 'MALFORMED'
    if 'optional' not in row:
        return 'MISSING'
    return 'TRUE' if row['optional'] is True else 'FALSE' if row['optional'] is False else 'MALFORMED'


CONTAINED_EDGES = frozenset({
    ('@modelcontextprotocol/sdk', '0690cbe02511a95d1ff199acf20b5a12ac4dfde1bbe30c82a0de73afa92dffc9',
     'peerDependencies', '@cfworker/json-schema', INSTALL + '/node_modules/.pnpm/node_modules/@modelcontextprotocol/sdk/package.json'),
    ('ws', 'a56a3fd55945a3ce177e3ca165dafae6f7eb03b7aefd58c092ac723d5741a6fb',
     'peerDependencies', 'bufferutil', INSTALL + '/node_modules/.pnpm/node_modules/ws/package.json'),
    ('ws', 'a56a3fd55945a3ce177e3ca165dafae6f7eb03b7aefd58c092ac723d5741a6fb',
     'peerDependencies', 'utf-8-validate', INSTALL + '/node_modules/.pnpm/node_modules/ws/package.json'),
    ('zustand', '2c7130cb149070446491c0556df3dc35939f8c7f1977fc9c6b6158e151116ac1',
     'peerDependencies', '@types/react', INSTALL + '/node_modules/.pnpm/node_modules/zustand/package.json'),
})


def closure(trust, stats=None, resolver=None, contained=False, census=False):
    started = time.monotonic()
    require(not census or stats is not None and resolver is None and not contained, 'CENSUS_MODE_BOUNDARY')
    if stats is not None:
        stats.update(closure_package_count=0, closure_edge_count=0, closure_elapsed_ms=0,
                     unresolved_dependency=None, declaring_manifest_sha256=None,
                     declaring_package=None, dependency_kind=None)
        if census:
            stats['unresolved_edges'] = []
    try:
        deadline = started + 30
        observed = set()
        if contained:
            stats['contained_edge_count'] = 0
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
                if census:
                    stats['census_context'] = census_context(anchor, manifest, manifest_digest, kind)
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
                        if census:
                            require(len(stats['unresolved_edges']) < 32, 'CENSUS_UNRESOLVED_BOUND')
                            record = unresolved_metadata(name, manifest.get('name'), kind, manifest_digest)
                            record.update(logical_anchor=anchor, optional_classification=optional_classification(manifest, name, kind))
                            stats['unresolved_edges'].append(record)
                            continue  # Census-only: missing packages and their transitive dependencies remain unproved.
                        stats.update(unresolved_metadata(name, manifest.get('name'), kind, manifest_digest))
                        if resolver is not None:
                            edge = (manifest.get('name'), manifest_digest, kind, name, anchor)
                            if contained:
                                require(edge in CONTAINED_EDGES, 'RESOLVER_EXACT_EDGE')
                                require(edge not in observed, 'RESOLVER_SKIP_REPEATED')
                            else:
                                require(edge[:4] == (
                                    '@modelcontextprotocol/sdk', '0690cbe02511a95d1ff199acf20b5a12ac4dfde1bbe30c82a0de73afa92dffc9',
                                    'peerDependencies', '@cfworker/json-schema'), 'RESOLVER_EXACT_EDGE')
                            metadata = manifest.get('peerDependenciesMeta')
                            require(type(metadata) is dict and type(metadata.get(name)) is dict
                                    and metadata[name].get('optional') is True, 'RESOLVER_OPTIONAL_DECLARATION')
                            trust.verify()
                            stats['resolver_attempted'] = True
                            if contained:
                                remaining = deadline - time.monotonic()
                                require(remaining > 0, 'CLOSURE_BOUND')
                                stats['resolver_paths'] = resolver(anchor, name, min(5, remaining))
                                require(time.monotonic() <= deadline, 'CLOSURE_BOUND')
                            else:
                                stats['resolver_paths'] = resolver(anchor, name)
                            stats['resolver_anchor'] = anchor
                            trust.verify()
                            if contained:
                                contained_resolver_paths(anchor, stats['resolver_paths'])
                                observed.add(edge)
                                stats['contained_edge_count'] = len(observed)
                                stats['contained_optional_peer_skipped'] = True
                                continue
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
        if contained:
            require(observed == CONTAINED_EDGES, 'RESOLVER_EXPECTED_EDGES_MISSING')
            require(time.monotonic() <= deadline, 'CLOSURE_BOUND')
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


def reject_envfile_directives(raw, sockets=False):
    text = raw.decode('utf-8-sig').replace('\r\n', '\n')
    require('\r' not in text and '\0' not in text, 'UNIT_SOURCE_ENCODING')
    pending, section = '', None
    for line in text.splitlines():
        if line.lstrip().startswith(('#', ';')):
            continue
        line = pending + line
        if line.endswith('\\'):
            require(not sockets, 'UNIT_SOURCE_CONTINUATION')
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
        require(not sockets or match[1].lower() != 'sockets', 'UNIT_SOURCE_SOCKETS')
    require(not pending and section is not None, 'UNIT_SOURCE_INCOMPLETE')


def envfile_absence_proof(unit, sockets=False):
    require(unit in {PILOT, UNIT, UNIT_V2, UNIT_V3}, 'UNIT_SOURCE_TARGET')
    props = show(unit, ['FragmentPath', 'DropInPaths', 'PassEnvironment'])
    expected = '/etc/systemd/system/' + PILOT if unit == PILOT else '/run/systemd/transient/' + unit
    require(props == {'FragmentPath': expected, 'DropInPaths': '', 'PassEnvironment': ''}, 'UNIT_SOURCE_BOUNDARY')
    source = Trusted()
    try:
        reject_envfile_directives(source.read(expected), sockets=sockets)
        source.verify()
        require(show(unit, ['FragmentPath', 'DropInPaths', 'PassEnvironment']) == props, 'UNIT_SOURCE_MAPPING_DRIFT')
        source.verify()
    finally:
        source.close()


def show(unit, keys):
    raw = command(['/usr/bin/systemctl', 'show', unit, '--all', '--no-pager', '--property=' + ','.join(keys)])
    values = dict(line.split('=', 1) for line in raw.splitlines() if '=' in line)
    missing = set(keys) - set(values)
    require(missing <= {'EnvironmentFiles', 'Sockets'}, 'UNIT_PROPERTIES_MISSING')
    if 'EnvironmentFiles' in missing:
        envfile_absence_proof(unit)
        values['EnvironmentFiles'] = ENV_SOURCE_PROOF
    if 'Sockets' in missing:
        envfile_absence_proof(unit, sockets=True)
        values['Sockets'] = SOCKET_SOURCE_PROOF
    if 'Sockets' in values:
        require(values['Sockets'] in {'', SOCKET_SOURCE_PROOF} and ('Sockets' in missing or values['Sockets'] == ''), 'SOCKETS_NOT_EMPTY')
    require(set(values) == set(keys), 'UNIT_PROPERTIES_MISSING')
    return values


def effective_properties(unit):
    values = show(unit, list(EFFECTIVE) + ['EnvironmentFiles', 'InvocationID', 'Description', 'MainPID', 'ControlGroup', 'ActiveState'])
    require(all(values[k] == v for k, v in EFFECTIVE.items() if k != 'Sockets')
            and values['Sockets'] in {'', SOCKET_SOURCE_PROOF} and values['EnvironmentFiles'] in {'', ENV_SOURCE_PROOF},
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


def group_pids(group, target):
    require(target in {UNIT, UNIT_V2, UNIT_V3} and group == '/system.slice/' + target, 'CGROUP_PATH')
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


def apply(v2=False, target=None):
    require(sys.platform == 'linux' and sys.version_info[:2] == (3, 12) and sys.flags.optimize == 0,
            'PYTHON_RUNTIME')
    require(os.geteuid() == 0 and os.getegid() == 0, 'ROOT_REQUIRED')
    require(socket.gethostname() == 'deepseek-harness-01', 'HOST_IDENTITY')
    require(target is None or v2 and target == UNIT_V3, 'RUNTIME_TARGET')
    target = target or (UNIT_V2 if v2 else UNIT)
    absence_check = None
    trust, owner, group, netfd, started = Trusted(), None, None, None, False
    observed_processes = {}
    result = {'status': 'BLOCKED', 'runtime': 'NOT PROVEN', 'checkpoints': []}
    if target == UNIT_V3:
        result.update(unit=target, primary_error_code=None, cleanup_error_code=None)
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
        if v2:
            absence_check = absent_resolver_ancestors(trust)
            def query(anchor, dependency, timeout):
                end = time.monotonic() + timeout
                absence_check()
                remaining = end - time.monotonic()
                require(remaining > 0, 'RESOLVER_TIMEOUT')
                paths = resolver_query(anchor, dependency, path, no_global=True, timeout=remaining)
                absence_check()
                return paths
            links, canonicals = closure(trust, result, query, contained=True)
            absence_check()
        else:
            links, canonicals = closure(trust)
        require(show(target, ['LoadState'])['LoadState'] == 'not-found', 'UNIT_ALREADY_EXISTS')
        candidate_inventory()
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')
        result['checkpoints'].append('PREFLIGHT_PASS')
        trust.verify()
        launch_before = snapshot(os.lstat(launch))
        require(launch_before == snapshot(s), 'LAUNCHER_DRIFT')
        args = ['/usr/bin/systemd-run', '--unit=' + target, '--description=' + description, '--quiet', '--no-block']
        args += ['--property=' + k + '=' + v for k, v in PROPERTIES.items()]
        candidate_argv = ([match[1], '--no-global-search-paths', match[2]] if v2 else [launch])
        candidate_argv += ['web', '--host', '127.0.0.1', '--port', '3081', '--no-open']
        args += ['--', '/usr/bin/env', '-i', 'HOME=/home/dsh', 'DSH_HOME=' + HOME, 'PATH=' + path] + candidate_argv
        if v2:
            absence_check()
        if target == UNIT_V3:
            require(show(target.removesuffix('.service') + '.socket', ['LoadState']) == {'LoadState': 'not-found'},
                    'SOCKET_UNIT_EXISTS')
        started = True
        command(args, 10)
        deadline = time.monotonic() + 30
        listener_pid, identity = None, None
        while time.monotonic() < deadline:
            if v2:
                owned = show(target, ['InvocationID', 'Description', 'Transient', 'ControlGroup'])
                require(owned['Description'] == description and owned['Transient'] == 'yes'
                        and re.fullmatch('[0-9a-f]{32}', owned['InvocationID']), 'UNIT_OWNERSHIP')
                owner, group = (owned['InvocationID'], description), owned['ControlGroup']
            unit = effective_properties(target)
            require(unit['Description'] == description and re.fullmatch('[0-9a-f]{32}', unit['InvocationID']), 'UNIT_OWNERSHIP')
            owner = unit['InvocationID'], description
            group = unit['ControlGroup']
            require(unit['ActiveState'] in {'active', 'activating'}, 'CANDIDATE_TERMINATED')
            pids = group_pids(group, target)
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
        require(process(listener_pid) == identity and listener_pid in group_pids(group, target), 'PROCESS_IDENTITY_DRIFT')
        status = dict(line.split(':', 1) for line in proc_read(listener_pid, 'status').decode().splitlines() if ':' in line)
        require(status['Uid'].split() == ['1000'] * 4 and status['Gid'].split() == ['1000'] * 4, 'LISTENER_UID_GID')
        validate_selector(environment(listener_pid), path)
        require(argv(listener_pid) == (candidate_argv if v2 else pilot_args[:-5] + ['web', '--host', '127.0.0.1', '--port', '3081', '--no-open']),
                'CANDIDATE_ARGV')
        validate_listener(listeners(listener_pid), socket_inodes(listener_pid))
        net_shape(listener_pid)
        require(not any(row[0].endswith(':0C09') for row in listeners('self')), 'HOST_LISTENER_CREATED')
        preprobe = effective_properties(target)
        validate_owned(preprobe, owner)
        require(preprobe['ControlGroup'] == group
                and preprobe['ActiveState'] == 'active', 'PREPROBE_UNIT_DRIFT')
        if preprobe['EnvironmentFiles'] == ENV_SOURCE_PROOF:
            result['checkpoints'].append('CANDIDATE_ENVIRONMENTFILES_ABSENT_SOURCE_VERIFIED')
        if target == UNIT_V3 and preprobe['Sockets'] == SOCKET_SOURCE_PROOF:
            result['checkpoints'].append('CANDIDATE_SOCKETS_ABSENT_SOURCE_VERIFIED')
        require(process(listener_pid) == identity, 'PREPROBE_IDENTITY_DRIFT')
        result['checkpoints'].append('ISOLATION_PASS')
        raw = command(['/usr/bin/nsenter', '--net=/proc/self/fd/' + str(netfd), '/usr/bin/python3.12', '-I', '-c', PROBE],
                      18, fds=(netfd,))
        require(json.loads(raw) == {'status': 'PASS', 'registered_route_count': 0, 'native_default_matches': True}, 'API_RECEIPT')
        result['checkpoints'].append('API_READBACK_PASS')
        result.update({'registered_route_count': 0, 'native_default_matches': True, 'status': 'PROBE_PASS_CLEANUP_PENDING'})
    except Blocked as error:
        result['error_code'] = diagnostic_error(error)['safe_code'] if v2 else str(error)
        if target == UNIT_V3:
            result['primary_error_code'] = result['error_code']
    except Exception as error:
        result['error_code'] = 'UNEXPECTED_FAILURE'
        if v2:
            result.update(diagnostic_error(error))
        if target == UNIT_V3:
            result['primary_error_code'] = result.get('safe_code') or 'UNEXPECTED_FAILURE'
    finally:
        if started:
            try:
                props = show(target, ['InvocationID', 'Description', 'Transient', 'ControlGroup'])
                if owner is None:
                    require(props['Description'] == description and props['Transient'] == 'yes'
                            and re.fullmatch('[0-9a-f]{32}', props['InvocationID']), 'CLEANUP_OWNERSHIP')
                    owner = props['InvocationID'], description
                    group = props['ControlGroup']
                validate_owned(props, owner)
                command(['/usr/bin/systemctl', 'stop', target], 30)
                state = show(target, ['LoadState', 'ActiveState'])
                require(state['ActiveState'] in {'inactive', 'failed'} or state['LoadState'] == 'not-found', 'UNIT_NOT_STOPPED')
                require(not group_pids(group, target), 'CGROUP_NOT_EMPTY')
                for pid, prior in observed_processes.items():
                    try:
                        remaining = process(pid)
                    except (FileNotFoundError, ProcessLookupError):
                        continue
                    require(remaining[1] != prior[1], 'CANDIDATE_PROCESS_REMAINS')
                if v2:
                    result['checkpoints'].append('OWNED_PROCESS_CLEANUP_PASS')
                    result['namespace_cleanup'] = 'NOT PROVEN'
                require(netfd is not None, 'HELD_NAMESPACE_UNAVAILABLE')
                check = "import pathlib,sys;sys.exit(any(l.split()[3]=='0A' and l.split()[1].endswith(':0C09') for n in ('tcp','tcp6') for l in pathlib.Path('/proc/self/net/'+n).read_text().splitlines()[1:]))"
                command(['/usr/bin/nsenter', '--net=/proc/self/fd/' + str(netfd), '/usr/bin/python3.12', '-I', '-c', check],
                        5, fds=(netfd,))
                if v2:
                    result['namespace_cleanup'] = 'PASS'
                    absence_check()
                    result['ancestor_absence_verified'] = True
                result['checkpoints'].append('OWNED_CLEANUP_PASS')
                if result['status'] == 'PROBE_PASS_CLEANUP_PENDING':
                    result['inventory'] = candidate_inventory(links, canonicals, trust)
                    result['checkpoints'].append('CONTAINMENT_METADATA_PASS')
                    result['status'] = 'ISOLATED_CANDIDATE_SMOKE_PASS'
                    result['runtime'] = 'ISOLATED_CONTAINMENT_ONLY'
            except Blocked as error:
                if target == UNIT_V3:
                    result['cleanup_error_code'] = diagnostic_error(error)['safe_code']
                result.update(status='CLEANUP_NOT_PROVEN' if 'OWNED_CLEANUP_PASS' not in result['checkpoints'] else 'BLOCKED',
                              error_code=diagnostic_error(error)['safe_code'] if v2 else str(error))
            except Exception:
                if target == UNIT_V3:
                    result['cleanup_error_code'] = 'CLEANUP_OR_INVENTORY_FAILURE'
                result.update(status='CLEANUP_NOT_PROVEN' if 'OWNED_CLEANUP_PASS' not in result['checkpoints'] else 'BLOCKED',
                              error_code='CLEANUP_OR_INVENTORY_FAILURE')
        if before is not None:
            try:
                require(pilot_baseline() == before, 'PILOT_CHANGED')
                result['checkpoints'].append('PILOT_IDENTITY_UNCHANGED')
            except Exception:
                result.update(status='BLOCKED' if result['status'] != 'CLEANUP_NOT_PROVEN' else result['status'],
                              pilot_error_code='PILOT_PRESERVATION_NOT_PROVEN')
        if v2:
            if absence_check is not None:
                try:
                    absence_check()
                    result['ancestor_absence_verified'] = True
                except Exception as error:
                    if target == UNIT_V3 and result['cleanup_error_code'] is None:
                        result['cleanup_error_code'] = diagnostic_error(error)['safe_code'] or 'SECONDARY_CLEANUP_FAILURE'
                    result.update(status='CLEANUP_NOT_PROVEN' if result['status'] == 'CLEANUP_NOT_PROVEN' else 'BLOCKED',
                                  absence_error=diagnostic_error(error))
            owned_fds = ([netfd] if netfd is not None else []) + [row[0] for row in reversed(list(trust.held.values()))]
            for fd in owned_fds:
                try:
                    os.close(fd)
                except Exception as error:
                    if target == UNIT_V3 and result['cleanup_error_code'] is None:
                        result['cleanup_error_code'] = diagnostic_error(error)['safe_code'] or 'SECONDARY_CLEANUP_FAILURE'
                    result.update(status='CLEANUP_NOT_PROVEN' if result['status'] == 'CLEANUP_NOT_PROVEN' else 'BLOCKED',
                                  descriptor_cleanup_error=diagnostic_error(error))
        else:
            if netfd is not None:
                os.close(netfd)
            trust.close()
    result['parent_http_and_tunnel_verification'] = 'REQUIRED_SEPARATELY'
    return result


DIAGNOSTIC_CODES = frozenset({
    'RUNTIME_TARGET', 'SECONDARY_CLEANUP_FAILURE', 'FD_LIMIT_RESTORE_FAILED',
    'UNIT_SOURCE_CONTINUATION', 'UNIT_SOURCE_SOCKETS', 'SOCKETS_NOT_EMPTY', 'SOCKET_SOURCE_INTERFACE', 'SOCKET_UNIT_EXISTS',
    'JOURNAL_SIZE', 'JOURNAL_ROWS', 'JOURNAL_FIELDS', 'JOURNAL_TARGET', 'JOURNAL_VALUE', 'JOURNAL_CURSOR',
    'JOURNAL_UNKNOWN_ENUM', 'JOURNAL_ID', 'JOURNAL_NUMBER', 'JOURNAL_INTERVAL', 'JOURNAL_TIMEOUT', 'JOURNAL_EXIT', 'JOURNAL_NO_EVIDENCE',
    'APPLIED_PROPERTIES',
    'CANDIDATE_ANCESTOR_DRIFT',
    'CANDIDATE_ANCESTOR_MODE',
    'CANDIDATE_ANCESTOR_OWNER',
    'CANDIDATE_ANCESTOR_TRUST',
    'CANDIDATE_ATTRIBUTES',
    'CANDIDATE_DIRECTORY_DRIFT',
    'CANDIDATE_HARDLINK',
    'CANDIDATE_LINK_ATTRIBUTES',
    'CANDIDATE_LINK_DRIFT',
    'CANDIDATE_MOUNT',
    'CANDIDATE_NOT_FRESH',
    'CANDIDATE_OPEN_DRIFT',
    'CANDIDATE_OWNER_DEVICE',
    'CANDIDATE_PATH_DRIFT',
    'CANDIDATE_PIN',
    'CANDIDATE_PRIVATE_MODE',
    'CANDIDATE_READ_DRIFT',
    'CANDIDATE_SPECIAL_FILE',
    'CGROUP_PATH',
    'CGROUP_V2_REQUIRED',
    'COMMAND_FAILED',
    'COMMAND_TIMEOUT',
    'DIAGNOSTIC_IDENTITY',
    'DUPLICATE_ENVIRONMENT',
    'FALLBACK_EXTRA_ENTRY',
    'FALLBACK_MAPPING',
    'FALLBACK_MISSING',
    'INVENTORY_BOUND',
    'LISTENER_OWNERSHIP',
    'NETWORK_INTERFACES',
    'NETWORK_IPV6_ROUTES',
    'NETWORK_ROUTES',
    'ORIGINAL_FILE_MISSING',
    'PILOT_ARGV',
    'PILOT_ENVIRONMENT',
    'PILOT_ENVIRONMENT_SOURCE',
    'PILOT_NOT_ACTIVE',
    'PILOT_PATH',
    'PILOT_PROPERTIES',
    'RUNTIME_DIGEST_DRIFT',
    'RUNTIME_HASH_BOUND',
    'RUNTIME_SIZE_BOUND',
    'SELECTOR_OR_ENVIRONMENT',
    'UNEXPECTED_CANDIDATE_LINK',
    'UNIT_PROPERTIES_MISSING',
    'UNIT_SOURCE_BOUNDARY',
    'UNIT_SOURCE_ENCODING',
    'UNIT_SOURCE_ENVIRONMENTFILE',
    'UNIT_SOURCE_INCLUDE',
    'UNIT_SOURCE_INCOMPLETE',
    'UNIT_SOURCE_MAPPING_DRIFT',
    'UNIT_SOURCE_SYNTAX',
    'UNIT_SOURCE_TARGET',

    'API_RECEIPT', 'CANDIDATE_ARGV', 'CANDIDATE_NAMESPACE_CGROUP', 'CANDIDATE_PROCESS_REMAINS', 'CANDIDATE_TERMINATED', 'CGROUP_NOT_EMPTY', 'CLEANUP_OWNERSHIP', 'HELD_NAMESPACE_UNAVAILABLE', 'HOST_3081_EXISTS', 'HOST_IDENTITY', 'HOST_LISTENER_CREATED', 'LAUNCHER_DRIFT', 'LAUNCHER_FIXED_EXEC', 'LAUNCHER_METADATA', 'LAUNCHER_REVIEWED_ENTRY', 'LAUNCHER_SHAPE', 'LAUNCHER_SHEBANG', 'LISTENER_TIMEOUT', 'LISTENER_UID_GID', 'MULTIPLE_LISTENER_OWNERS', 'NAMESPACE_FD_IDENTITY', 'NODE_EXECUTABLE', 'NODE_RUNTIME_PIN', 'PILOT_CHANGED', 'PILOT_NAMESPACE', 'PILOT_REVIEWED_ENTRY', 'PREPROBE_IDENTITY_DRIFT', 'PREPROBE_UNIT_DRIFT', 'PROCESS_IDENTITY_DRIFT', 'PYTHON_RUNTIME', 'RESOLVER_TIMEOUT', 'REVIEWED_LOGICAL_MAPPING', 'ROOT_REQUIRED', 'SOURCE_PIN', 'SOURCE_PINS_MISSING', 'TOOL_EXECUTABLE', 'UNIT_ALREADY_EXISTS', 'UNIT_NOT_STOPPED', 'UNIT_OWNERSHIP', 'WORKSPACE_ENVFILE',
    'CLOSURE_BOUND', 'PACKAGE_BOUND', 'PACKAGE_NAME', 'DEPENDENCY_MAP', 'DEPENDENCY_VERSION',
    'MANIFEST_IDENTITY', 'REVIEWED_PACKAGE_MAPPING', 'REVIEWED_CLOSURE_MAPPING', 'INSTALLED_ONLY_RESOLUTION',
    'TRUST_PATH', 'TRUST_OWNER_MODE', 'TRUST_TYPE', 'TRUST_LINK_COUNT', 'TRUST_ATTRIBUTES',
    'TRUST_METADATA_DRIFT', 'TRUST_LINK_DRIFT', 'INSTALL_ESCAPE', 'LINK_OUTSIDE_INSTALL', 'LINK_OWNER',
    'LINK_ATTRIBUTES', 'LINK_DRIFT', 'LINK_ESCAPE', 'LINK_BOUND', 'PACKAGE_DIRECTORY_TYPE',
    'READ_BOUND', 'SOURCE_DIGEST_DRIFT', 'SOURCE_PIN', 'SOURCE_PINS_MISSING',
    'DIAGNOSTIC_FD_HARD_LIMIT', 'DIAGNOSTIC_FD_LIMIT_MISMATCH', 'DIAGNOSTIC_FD_RESTORE_MISMATCH',
    'DIAGNOSTIC_PACKAGE_NAME_BOUND',
    'DIAGNOSTIC_DEPENDENCY_KIND', 'DIAGNOSTIC_MANIFEST_DIGEST',
    'RESOLVER_EXACT_EDGE', 'RESOLVER_OPTIONAL_DECLARATION', 'RESOLVER_PATH', 'RESOLVER_ANCHOR',
    'RESOLVER_RESPONSE', 'RESOLVER_SIZE', 'RESOLVER_TIMEOUT', 'RESOLVER_EXIT', 'RESOLVER_CLEANUP',
    'RESOLVER_ANCESTOR_EXISTS', 'RESOLVER_MOUNT_DRIFT', 'RESOLVER_CONTAINED_PATHS',
    'RESOLVER_SKIP_REPEATED', 'RESOLVER_EXPECTED_EDGES_MISSING',
    'CENSUS_MODE_BOUNDARY', 'CENSUS_UNRESOLVED_BOUND',
})


RESOLVER_CODE = "const m=require('node:module');process.stdout.write(JSON.stringify(m.createRequire(process.argv[1]).resolve.paths(process.argv[2])));"


def resolver_path(value):
    require(type(value) is str and len(value) <= 4096 and value.startswith('/') and not value.startswith('//')
            and pp.normpath(value) == value and re.fullmatch(r'/[A-Za-z0-9._/@+-]*', value), 'RESOLVER_PATH')


def resolver_output(raw):
    require(len(raw) <= 16384, 'RESOLVER_SIZE')
    paths = json.loads(raw)
    require(type(paths) is list and 0 < len(paths) <= 64, 'RESOLVER_RESPONSE')
    for path in paths:
        resolver_path(path)
    require(len(set(paths)) == len(paths), 'RESOLVER_RESPONSE')
    return paths


def contained_resolver_paths(anchor, paths):
    installed = list(lookup_paths(anchor))
    require(installed and paths == installed + ['/opt/node_modules', '/node_modules'],
            'RESOLVER_CONTAINED_PATHS')


def absent_resolver_ancestors(trust):
    """Hold only the two trusted parents; never traverse the absent search roots."""
    parents = [(trust.open('/opt'), 'node_modules'), (trust.open('/'), 'node_modules')]

    def mounts():
        fd = os.open('/proc/self/mountinfo', os.O_RDONLY | os.O_CLOEXEC)
        try:
            raw = bounded_read(fd, 1048576).decode('utf-8')
        finally:
            os.close(fd)
        rows = []
        for line in raw.splitlines():
            target = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), line.split()[4])
            if target in {'/', '/opt', '/opt/node_modules', '/node_modules'}:
                rows.append(line)
        return tuple(rows)

    original_mounts = mounts()

    def verify():
        trust.verify()
        require(mounts() == original_mounts, 'RESOLVER_MOUNT_DRIFT')
        for fd, name in parents:
            try:
                os.stat(name, dir_fd=fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise Blocked('RESOLVER_ANCESTOR_EXISTS')
        trust.verify()
    verify()
    return verify


def resolver_query(anchor, dependency, path, no_global=False, timeout=5):
    """Core Node path-list query only: no package resolution or root inspection."""
    resolver_path(anchor)
    require(anchor.startswith(INSTALL + '/') and pp.basename(anchor) == 'package.json'
            and ((anchor, dependency) in {(e[4], e[3]) for e in CONTAINED_EDGES} if no_global
                 else dependency == '@cfworker/json-schema'), 'RESOLVER_ANCHOR')
    arguments = (['/opt/node-v24.19.0-linux-x64/bin/node'] + (['--no-global-search-paths'] if no_global else [])
                 + ['--input-type=commonjs', '-e', RESOLVER_CODE, anchor, dependency])
    require(0 < timeout <= 5, 'RESOLVER_TIMEOUT')
    end = time.monotonic() + timeout
    proc, poller = None, None
    try:
        proc = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                cwd='/srv/dsh/workspaces', env={'HOME': '/home/dsh', 'DSH_HOME': HOME, 'PATH': path},
                                user=1000, group=1000, extra_groups=[], close_fds=True, pass_fds=())
        poller = selectors.DefaultSelector()
        os.set_blocking(proc.stdout.fileno(), False)
        poller.register(proc.stdout, selectors.EVENT_READ)
        raw = bytearray()
        while True:
            remaining = end - time.monotonic()
            require(remaining > 0, 'RESOLVER_TIMEOUT')
            require(poller.select(remaining), 'RESOLVER_TIMEOUT')
            chunk = os.read(proc.stdout.fileno(), min(4096, 16385 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
            require(len(raw) <= 16384, 'RESOLVER_SIZE')
        remaining = end - time.monotonic()
        require(remaining > 0, 'RESOLVER_TIMEOUT')
        try:
            code = proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            raise Blocked('RESOLVER_TIMEOUT') from None
        require(code == 0, 'RESOLVER_EXIT')
        return resolver_output(raw)
    finally:
        try:
            if proc is not None and proc.poll() is None:
                proc.kill()
                try:
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    raise Blocked('RESOLVER_CLEANUP') from None
        finally:
            if poller is not None:
                poller.close()
            if proc is not None:
                proc.stdout.close()


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


def socket_source_diagnostic():
    result = {'status': 'SOCKET_SOURCE_DIAGNOSTIC_INCOMPLETE', 'proofs': {}, 'runtime_acceptance': 'NOT PROVEN'}
    try:
        require(sys.platform == 'linux' and os.geteuid() == 0 and socket.gethostname() == 'deepseek-harness-01',
                'DIAGNOSTIC_IDENTITY')
        keys = ['EnvironmentFiles', 'Sockets', 'TriggeredBy', 'PassEnvironment', 'DropInPaths', 'ActiveState']
        props = show(PILOT, keys)
        require(props['ActiveState'] == 'active' and props['EnvironmentFiles'] in {'', ENV_SOURCE_PROOF}
                and props['Sockets'] in {'', SOCKET_SOURCE_PROOF}
                and props['TriggeredBy'] == props['PassEnvironment'] == props['DropInPaths'] == '', 'SOCKET_SOURCE_INTERFACE')
        envfile_absence_proof(PILOT, sockets=True)
        require(show(PILOT, keys) == props, 'UNIT_SOURCE_MAPPING_DRIFT')
        prospective = UNIT_V3.removesuffix('.service') + '.socket'
        require(show(prospective, ['LoadState']) == {'LoadState': 'not-found'}, 'SOCKET_UNIT_EXISTS')
        result['proofs'] = {'EnvironmentFiles': props['EnvironmentFiles'] or 'EMITTED_EMPTY',
                            'Sockets': props['Sockets'] or 'EMITTED_EMPTY', 'TriggeredBy': 'EMITTED_EMPTY',
                            'FragmentDirectives': 'ABSENT_SOURCE_VERIFIED', 'ProspectiveSocket': 'NOT_FOUND'}
        result['status'] = 'SOCKET_SOURCE_DIAGNOSTIC_PASS'
    except Exception as error:
        result.update(diagnostic_error(error))
    return result


JOURNAL_FIELDS = ('__REALTIME_TIMESTAMP', '__MONOTONIC_TIMESTAMP', '_PID', '_UID', '_GID', 'UNIT',
                  'MESSAGE_ID', '_BOOT_ID', 'JOB_TYPE', 'JOB_RESULT', 'UNIT_RESULT', 'RESULT', 'ERRNO', 'EXIT_CODE', 'EXIT_STATUS')
JOURNAL_ENUMS = {
    'JOB_TYPE': {'start', 'stop', 'restart', 'try-restart', 'reload', 'reload-or-start', 'verify-active', 'nop'},
    'JOB_RESULT': {'done', 'canceled', 'timeout', 'failed', 'dependency', 'skipped', 'invalid', 'assert', 'unsupported', 'collected', 'once'},
    'UNIT_RESULT': {'success', 'resources', 'timeout', 'exit-code', 'signal', 'core-dump', 'watchdog', 'start-limit-hit', 'oom-kill', 'protocol', 'exec-condition'},
    'RESULT': {'success', 'resources', 'timeout', 'exit-code', 'signal', 'core-dump', 'watchdog', 'start-limit-hit', 'oom-kill', 'protocol', 'exec-condition'},
    'EXIT_CODE': {'exited', 'killed', 'dumped'},
}


def journal_records(raw):
    require(len(raw) <= 65536, 'JOURNAL_SIZE')
    lines = raw.splitlines()
    require(len(lines) <= 128, 'JOURNAL_ROWS')
    records = []
    for line in lines:
        row = json.loads(line)
        require(type(row) is dict and set(row) <= set(JOURNAL_FIELDS) | {'__CURSOR'}, 'JOURNAL_FIELDS')
        require(row.get('_PID') == '1' and row.get('UNIT') == UNIT_V2, 'JOURNAL_TARGET')
        out = {field: None for field in JOURNAL_FIELDS}
        for key, value in row.items():
            require(type(value) is str and len(value) <= 512, 'JOURNAL_VALUE')
            if key == '__CURSOR':
                require(re.fullmatch(r'[a-zA-Z0-9=;_-]+', value), 'JOURNAL_CURSOR')
                continue
            if key in JOURNAL_ENUMS:
                require(value in JOURNAL_ENUMS[key], 'JOURNAL_UNKNOWN_ENUM')
                out[key] = value
            elif key in {'MESSAGE_ID', '_BOOT_ID'}:
                require(re.fullmatch('[0-9a-f]{32}', value), 'JOURNAL_ID')
                out[key] = value
            elif key == 'UNIT':
                out[key] = value
            else:
                require(re.fullmatch('[0-9]{1,20}', value), 'JOURNAL_NUMBER')
                number = int(value)
                require(number <= (255 if key == 'EXIT_STATUS' else 4095 if key == 'ERRNO' else 2**64 - 1), 'JOURNAL_NUMBER')
                out[key] = number
        # Exact fixed UTC evidence interval, expressed as Unix microseconds.
        require(type(out['__REALTIME_TIMESTAMP']) is int
                and 1788895020000000 <= out['__REALTIME_TIMESTAMP'] <= 1788895140000000, 'JOURNAL_INTERVAL')
        require(out['_BOOT_ID'] is not None, 'JOURNAL_ID')
        records.append(out)
    return records


def attempt_journal_diagnostic():
    """Read only the exact v2 PID-1 lifecycle fields; never request journal MESSAGE."""
    result = {'status': 'ATTEMPT_JOURNAL_INCOMPLETE', 'unit': UNIT_V2, 'records': [],
              'boot_binding': 'NOT PROVEN', 'runtime_acceptance': 'NOT PROVEN'}
    trust, proc, poller = Trusted(), None, None
    try:
        require(sys.platform == 'linux' and os.geteuid() == 0 and socket.gethostname() == 'deepseek-harness-01',
                'DIAGNOSTIC_IDENTITY')
        fd = trust.open('/usr/bin/journalctl', True)
        require(os.fstat(fd).st_mode & 0o111, 'TOOL_EXECUTABLE')
        trust.verify()
        end = time.monotonic() + 5
        proc = subprocess.Popen(['/usr/bin/journalctl', '--quiet', '--no-pager', '--output=json',
                                 '--output-fields=' + ','.join(JOURNAL_FIELDS),
                                 '--since=2026-09-08 19:17:00 UTC', '--until=2026-09-08 19:19:00 UTC',
                                 '_PID=1', 'UNIT=' + UNIT_V2],
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                env={'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'TZ': 'UTC'}, cwd='/',
                                close_fds=True, pass_fds=())
        poller = selectors.DefaultSelector()
        os.set_blocking(proc.stdout.fileno(), False)
        poller.register(proc.stdout, selectors.EVENT_READ)
        raw = bytearray()
        while True:
            remaining = end - time.monotonic()
            require(remaining > 0 and poller.select(remaining), 'JOURNAL_TIMEOUT')
            chunk = os.read(proc.stdout.fileno(), min(4096, 65537 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
            require(len(raw) <= 65536, 'JOURNAL_SIZE')
            require(raw.count(b'\n') <= 128, 'JOURNAL_ROWS')
        remaining = end - time.monotonic()
        require(remaining > 0, 'JOURNAL_TIMEOUT')
        try:
            exit_code = proc.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            raise Blocked('JOURNAL_TIMEOUT') from None
        require(exit_code == 0, 'JOURNAL_EXIT')
        records = journal_records(raw)
        trust.verify()
        result['records'] = records
        require(records, 'JOURNAL_NO_EVIDENCE')
        result['status'] = 'ATTEMPT_JOURNAL_COMPLETE'
    except Exception as error:
        result.update(diagnostic_error(error))
    finally:
        try:
            if proc is not None and proc.poll() is None:
                proc.kill()
                proc.wait(timeout=1)
        except Exception as error:
            result.update(status='ATTEMPT_JOURNAL_INCOMPLETE', cleanup_error=diagnostic_error(error))
        finally:
            for owned in ([poller] if poller is not None else []) + ([proc.stdout] if proc is not None else []):
                try:
                    owned.close()
                except Exception as error:
                    result.update(status='ATTEMPT_JOURNAL_INCOMPLETE', cleanup_error=diagnostic_error(error))
            for fd, _, _ in reversed(list(trust.held.values())):
                try:
                    os.close(fd)
                except Exception as error:
                    result.update(status='ATTEMPT_JOURNAL_INCOMPLETE', cleanup_error=diagnostic_error(error))
    return result


def apply_v2(target=UNIT_V2):
    """Separate explicit runtime attempt, with process-local limits restored after owned FDs close."""
    require(target in {UNIT_V2, UNIT_V3}, 'RUNTIME_TARGET')
    import resource
    original, attempted = resource.getrlimit(resource.RLIMIT_NOFILE), False
    result = {'status': 'BLOCKED', 'runtime': 'NOT PROVEN', 'unit': target,
              'fd_soft_limit': original[0], 'fd_hard_limit': original[1]}
    try:
        require(original[1] >= 4096, 'DIAGNOSTIC_FD_HARD_LIMIT')
        attempted = True
        resource.setrlimit(resource.RLIMIT_NOFILE, (4096, original[1]))
        require(resource.getrlimit(resource.RLIMIT_NOFILE) == (4096, original[1]), 'DIAGNOSTIC_FD_LIMIT_MISMATCH')
        result.update(fd_applied_soft_limit=4096, fd_applied_hard_limit=original[1])
        result.update(apply(v2=True, target=target) if target == UNIT_V3 else apply(v2=True))
    except Exception as error:
        result.update(status='BLOCKED', **diagnostic_error(error))
        if target == UNIT_V3:
            result.setdefault('primary_error_code', result.get('safe_code') or 'UNEXPECTED_FAILURE')
    finally:
        if attempted:
            result['fd_restoration'] = 'PASS'
            try:
                resource.setrlimit(resource.RLIMIT_NOFILE, original)
                restored = resource.getrlimit(resource.RLIMIT_NOFILE)
                result['fd_restored_soft_limit'], result['fd_restored_hard_limit'] = restored
                require(restored == original, 'DIAGNOSTIC_FD_RESTORE_MISMATCH')
            except Exception as error:
                if target == UNIT_V3 and result.get('cleanup_error_code') is None:
                    result['cleanup_error_code'] = 'FD_LIMIT_RESTORE_FAILED'
                result.update(status='CLEANUP_NOT_PROVEN' if result['status'] == 'CLEANUP_NOT_PROVEN' else 'FD_LIMIT_RESTORE_FAILED',
                              fd_restoration='FAILED', restoration_error=diagnostic_error(error))
    return result


def preflight_diagnostic(resolver_diagnostic=False, contained_diagnostic=False, unresolved_census=False):
    """Read-only reproduction: this entry has no path to apply or unit controls."""
    result = {'status': 'DIAGNOSTIC_BLOCKED', 'stage': 'RUNTIME', 'exception_class': None, 'errno': None, 'safe_code': None,
              'closure_package_count': None, 'closure_edge_count': None, 'closure_elapsed_ms': None,
              'unresolved_dependency': None, 'declaring_manifest_sha256': None,
              'declaring_package': None, 'dependency_kind': None,
              'resolver_attempted': False, 'resolver_anchor': None, 'resolver_paths': None,
              'contained_optional_peer_skipped': False, 'ancestor_absence_verified': False,
              'held_fd_count': 0, 'last_successful_fd_count': None, 'fd_soft_limit': None, 'fd_hard_limit': None,
              'fd_applied_soft_limit': None, 'fd_applied_hard_limit': None,
              'fd_restored_soft_limit': None, 'fd_restored_hard_limit': None,
              'fd_restoration': 'NOT_ATTEMPTED'}
    trust, previous_handler, original_limits, limit_attempted = Trusted(), None, None, False
    absence_check = None
    if unresolved_census:
        result.update(status='UNRESOLVED_CENSUS_INCOMPLETE', unresolved_edges=[], census_context=None,
                      census_scope='REACHABLE_INSTALLED_MANIFESTS_ONLY', runtime_acceptance='NOT PROVEN',
                      missing_package_transitives='NOT_ENUMERATED')

    def stage(name):
        result['stage'] = name
        try:
            result['last_successful_fd_count'] = len(os.listdir('/proc/self/fd'))
        except OSError:
            pass  # Keep the last successful observation; do not adapt limits to observed usage.

    def deadline(*unused):
        raise TimeoutError()

    try:
        require(sum((resolver_diagnostic, contained_diagnostic, unresolved_census)) <= 1, 'CENSUS_MODE_BOUNDARY')
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
        if contained_diagnostic:
            stage('RESOLVER_ANCESTOR_ABSENCE')
            absence_check = absent_resolver_ancestors(trust)
        def query(anchor, dependency, timeout=5):
            query_deadline = time.monotonic() + timeout
            if absence_check is not None:
                absence_check()
                timeout = query_deadline - time.monotonic()
                require(timeout > 0, 'RESOLVER_TIMEOUT')
            paths = resolver_query(anchor, dependency, path, no_global=contained_diagnostic, timeout=timeout)
            if absence_check is not None:
                absence_check()
            return paths
        stage('INSTALLED_CLOSURE')
        closure(trust, result, query if resolver_diagnostic or contained_diagnostic else None,
                contained=contained_diagnostic, census=unresolved_census)
        stage('UNIT_ABSENCE')
        require(show(UNIT, ['LoadState'])['LoadState'] == 'not-found', 'UNIT_ALREADY_EXISTS')
        stage('FINAL_CANDIDATE_INVENTORY')
        candidate_inventory()
        require(not os.path.lexists('/srv/dsh/workspaces/.env'), 'WORKSPACE_ENVFILE')
        stage('FINAL_HELD_METADATA')
        trust.verify()
        result['status'] = 'UNRESOLVED_CENSUS_COMPLETE' if unresolved_census else 'READ_ONLY_PREFLIGHT_PASS'
    except Exception as error:
        result.update(diagnostic_error(error))
    finally:
        result['held_fd_count'] = len(trust.held)
        if absence_check is not None:
            try:
                absence_check()
                result['ancestor_absence_verified'] = True
            except Exception as error:
                if result['exception_class'] is None:
                    result.update(diagnostic_error(error))
                result['status'] = 'DIAGNOSTIC_BLOCKED'
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
    if unresolved_census and result['status'] != 'UNRESOLVED_CENSUS_COMPLETE':
        result['status'] = 'UNRESOLVED_CENSUS_INCOMPLETE'
    return result


def self_test():
    import contextlib
    import io
    import urllib.request
    from types import SimpleNamespace
    from unittest.mock import patch
    for omitted in (set(), {'EnvironmentFiles'}, {'Sockets'}, {'EnvironmentFiles', 'Sockets'}):
        source_calls = []
        keys = ['EnvironmentFiles', 'Sockets', 'TriggeredBy']
        with patch.dict(globals(), {'command': lambda *args: ''.join(k + '=\n' for k in keys if k not in omitted),
                                   'envfile_absence_proof': lambda unit, sockets=False: source_calls.append((unit, sockets))}):
            shown = show(PILOT, keys)
        require(shown['EnvironmentFiles'] == (ENV_SOURCE_PROOF if 'EnvironmentFiles' in omitted else '')
                and shown['Sockets'] == (SOCKET_SOURCE_PROOF if 'Sockets' in omitted else '')
                and len(source_calls) == len(omitted), 'SELF_TEST_INDEPENDENT_SOURCE_PROOFS')
    for raw in ('Sockets=unexpected.socket\nTriggeredBy=\nEnvironmentFiles=\n', 'Sockets=\nEnvironmentFiles=\n'):
        with patch.dict(globals(), {'command': lambda *args: raw, 'envfile_absence_proof': lambda *a, **kw: None}):
            try:
                show(PILOT, ['EnvironmentFiles', 'Sockets', 'TriggeredBy'])
            except Blocked:
                pass
            else:
                raise Blocked('SELF_TEST_SOCKET_INTERFACE_ACCEPTED')
    for raw in (b'[Service]\nSockets=\n', b'[Service]\nSockets=x.socket\n',
                b'[Service]\nExecStart=/bin/true \\\n ignored\n', b'.include /other\n'):
        try:
            reject_envfile_directives(raw, sockets=True)
        except Blocked:
            pass
        else:
            raise Blocked('SELF_TEST_SOCKET_DIRECTIVE_ACCEPTED')
    reject_envfile_directives(b'[Service]\nExecStart=/bin/true\n', sockets=True)
    journal_row = {'_PID': '1', 'UNIT': UNIT_V2, '__REALTIME_TIMESTAMP': '1788895080000000', '_BOOT_ID': 'a' * 32}
    journal_raw = json.dumps(journal_row).encode() + b'\n'
    require(journal_records(journal_raw)[0]['JOB_RESULT'] is None, 'SELF_TEST_JOURNAL_OPTIONAL')
    for mutation in ({'MESSAGE': 'private text'}, {'_PID': '2'}, {'UNIT': UNIT}, {'JOB_RESULT': 'private text'},
                     {'MESSAGE_ID': 'X' * 32}, {'__REALTIME_TIMESTAMP': '1788895140000001'}):
        try:
            journal_records(json.dumps(journal_row | mutation).encode())
        except Blocked:
            pass
        else:
            raise Blocked('SELF_TEST_JOURNAL_VALIDATION')
    for chunks, expected in (([journal_raw, b''], None), ([b''], 'JOURNAL_NO_EVIDENCE'),
                             ([b'x' * 4096] * 17, 'JOURNAL_SIZE'), ([b'\n' * 129], 'JOURNAL_ROWS')):
        fake_stream = SimpleNamespace(fileno=lambda: 71, close=lambda: None)
        journal_proc = SimpleNamespace(stdout=fake_stream, wait=lambda **kw: 0, poll=lambda: 0)
        journal_poller = SimpleNamespace(register=lambda *a: None, select=lambda _: True, close=lambda: None)
        with patch.dict(globals(), {'Trusted': lambda: SimpleNamespace(held={}, open=lambda *a: 71, verify=lambda: None)}), \
             patch.object(sys, 'platform', 'linux'), patch.object(os, 'geteuid', return_value=0, create=True), \
             patch.object(socket, 'gethostname', return_value='deepseek-harness-01'), \
             patch.object(os, 'fstat', return_value=SimpleNamespace(st_mode=0o100755)), \
             patch.object(os, 'set_blocking'), patch.object(os, 'read', side_effect=chunks), \
             patch.object(selectors, 'DefaultSelector', return_value=journal_poller), \
             patch.object(subprocess, 'Popen', return_value=journal_proc) as journal_start:
            receipt = attempt_journal_diagnostic()
        command_args = journal_start.call_args.args[0]
        require('_PID=1' in command_args and 'UNIT=' + UNIT_V2 in command_args
                and '--since=2026-09-08 19:17:00 UTC' in command_args
                and '--until=2026-09-08 19:19:00 UTC' in command_args
                and 'MESSAGE' not in next(x.split('=', 1)[1].split(',') for x in command_args if x.startswith('--output-fields='))
                and journal_start.call_args.kwargs['pass_fds'] == () and journal_start.call_args.kwargs['close_fds'] is True,
                'SELF_TEST_JOURNAL_SOURCE_FILTER')
        require(receipt['status'] == ('ATTEMPT_JOURNAL_COMPLETE' if expected is None else 'ATTEMPT_JOURNAL_INCOMPLETE')
                and (expected is None or receipt['safe_code'] == expected), 'SELF_TEST_JOURNAL_BOUNDS')
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
    require(resolver_output(b'["/home/dsh/.node_modules"]') == ['/home/dsh/.node_modules'], 'SELF_TEST_RESOLVER_OUTPUT')
    contained_anchor = INSTALL + '/node_modules/.pnpm/node_modules/@modelcontextprotocol/sdk/package.json'
    six_paths = list(lookup_paths(contained_anchor)) + ['/opt/node_modules', '/node_modules']
    contained_resolver_paths(contained_anchor, six_paths)
    for optional in (False, True):
        sdk = {'name': '@modelcontextprotocol/sdk', 'peerDependencies': {'@cfworker/json-schema': '^4.1.1'},
               'peerDependenciesMeta': {'@cfworker/json-schema': {'optional': optional}}}
        def unresolved_sdk(*unused):
            raise FileNotFoundError()
        sdk_trust = SimpleNamespace(read=lambda _: json.dumps(sdk).encode(), resolve=unresolved_sdk, verify=lambda: None)
        sdk_stats = {}
        # Synthetic exact-edge fixture: mock the digest interface, never a live pin.
        with patch.dict(globals(), {'PACKAGE': pp.dirname(contained_anchor), 'KNOWN_MAPPINGS': {}}), \
             patch.object(hashlib, 'sha256', return_value=SimpleNamespace(hexdigest=lambda: '0690cbe02511a95d1ff199acf20b5a12ac4dfde1bbe30c82a0de73afa92dffc9')):
            try:
                links, _ = closure(sdk_trust, sdk_stats, lambda a, d, t: six_paths, contained=True)
            except Blocked as error:
                require(error.args == (('RESOLVER_EXPECTED_EDGES_MISSING',) if optional else ('RESOLVER_OPTIONAL_DECLARATION',)),
                        'SELF_TEST_CONTAINED_OPTIONAL')
            else:
                require(optional and sdk_stats['contained_optional_peer_skipped'] is True
                        and set(links) == {'@modelcontextprotocol/sdk'}, 'SELF_TEST_CONTAINED_EXACT_SKIP')
    # Exercise the complete reviewed table through the actual FIFO closure.
    roots = {edge[0]: pp.dirname(edge[4]) for edge in CONTAINED_EDGES}
    digests = {edge[0]: edge[1] for edge in CONTAINED_EDGES}
    class RepeatedQueue(collections.deque):
        repeated = False
        def popleft(self):
            item = super().popleft()
            if variant == 'duplicate' and item[1]['name'] == 'ws' and not self.repeated:
                self.appendleft(item)
                self.repeated = True
            return item
    for variant, expected in ((None, None), ('missing', 'RESOLVER_EXPECTED_EDGES_MISSING'),
                              ('extra', 'RESOLVER_EXACT_EDGE'), ('duplicate', 'RESOLVER_SKIP_REPEATED'),
                              ('optional', 'RESOLVER_OPTIONAL_DECLARATION'), ('deadline', 'CLOSURE_BOUND')):
        manifests = {name: {'name': name, 'version': 'fixture', 'peerDependencies': {}, 'peerDependenciesMeta': {}}
                     for name in roots}
        for owner, digest, kind, dep, anchor in CONTAINED_EDGES:
            manifests[owner][kind][dep] = '*'
            manifests[owner]['peerDependenciesMeta'][dep] = {'optional': True}
        manifests['@modelcontextprotocol/sdk']['dependencies'] = {'ws': '*', 'zustand': '*'}
        if variant == 'missing':
            del manifests['ws']['peerDependencies']['bufferutil']
        if variant == 'extra':
            manifests['ws']['peerDependencies']['unexpected-peer'] = '*'
        if variant == 'optional':
            manifests['ws']['peerDependenciesMeta']['bufferutil']['optional'] = False
        def fixture_resolve(logical):
            if logical in roots.values():
                return logical
            raise FileNotFoundError()
        fixture_trust = SimpleNamespace(read=lambda path: next(name.encode() for name, root in roots.items()
                                                               if path == root + '/package.json'),
                                        resolve=fixture_resolve, verify=lambda: None)
        calls, ticks = [], [0]
        def fixture_query(anchor, dependency, timeout):
            require(0 < timeout <= 5 and len(calls) < 4, 'SELF_TEST_QUERY_BOUNDS')
            calls.append((anchor, dependency))
            if variant == 'deadline':
                ticks[0] = 31
            return list(lookup_paths(anchor)) + ['/opt/node_modules', '/node_modules']
        with patch.dict(globals(), {'PACKAGE': roots['@modelcontextprotocol/sdk'], 'KNOWN_MAPPINGS': {}}), \
             patch.object(collections, 'deque', RepeatedQueue), \
             patch.object(json, 'loads', side_effect=lambda raw: manifests[raw.decode()]), \
             patch.object(hashlib, 'sha256', side_effect=lambda raw: SimpleNamespace(hexdigest=lambda: digests[raw.decode()])), \
             patch.object(time, 'monotonic', side_effect=lambda: ticks[0]):
            fixture_stats = {}
            try:
                closure(fixture_trust, fixture_stats, fixture_query, contained=True)
            except Blocked as error:
                require(expected is not None and error.args == (expected,), 'SELF_TEST_FOUR_EDGE_REJECTION')
            else:
                require(expected is None and fixture_stats['contained_edge_count'] == 4 and len(set(calls)) == 4,
                        'SELF_TEST_FOUR_EDGE_COMPLETE')
    mount_bytes = [b'1 0 0:1 / / rw - ext4 /dev/root rw\n']
    ancestor_trust = SimpleNamespace(open=lambda path: 70 if path == '/opt' else 71, verify=lambda: None)
    with patch.object(os, 'open', return_value=72), patch.object(os, 'close'), patch.object(os, 'O_CLOEXEC', 0, create=True), \
         patch.dict(globals(), {'bounded_read': lambda fd, cap: mount_bytes[0]}), \
         patch.object(os, 'stat', side_effect=FileNotFoundError()) as absent_stat:
        verify_absent = absent_resolver_ancestors(ancestor_trust)
        verify_absent()
        absent_stat.side_effect = None
        absent_stat.return_value = SimpleNamespace()
        try:
            verify_absent()
        except Blocked as error:
            require(error.args == ('RESOLVER_ANCESTOR_EXISTS',), 'SELF_TEST_ANCESTOR_PRESENCE')
        else:
            raise RuntimeError('existing ancestor accepted')
        absent_stat.side_effect = FileNotFoundError()
        mount_bytes[0] += b'2 1 0:1 /opt /opt rw - ext4 /dev/root rw\n'
        try:
            verify_absent()
        except Blocked as error:
            require(error.args == ('RESOLVER_MOUNT_DRIFT',), 'SELF_TEST_ANCESTOR_MOUNT')
        else:
            raise RuntimeError('mount drift accepted')
    with patch.object(subprocess, 'Popen', side_effect=Blocked('SELF_TEST_NO_EXEC')) as launch:
        try:
            resolver_query(PACKAGE + '/package.json', '@cfworker/json-schema', '/usr/bin')
        except Blocked as error:
            require(error.args == ('SELF_TEST_NO_EXEC',), 'SELF_TEST_RESOLVER_NO_EXEC')
        else:
            raise RuntimeError('mock resolver launch did not stop')
    args, kwargs = launch.call_args
    require(args[0] == ['/opt/node-v24.19.0-linux-x64/bin/node', '--input-type=commonjs', '-e', RESOLVER_CODE,
                        PACKAGE + '/package.json', '@cfworker/json-schema']
            and kwargs['env'] == {'HOME': '/home/dsh', 'DSH_HOME': HOME, 'PATH': '/usr/bin'}
            and kwargs['user'] == kwargs['group'] == 1000 and kwargs['extra_groups'] == []
            and kwargs['close_fds'] is True and kwargs['pass_fds'] == ()
            and kwargs['cwd'] == '/srv/dsh/workspaces' and kwargs['stdin'] == kwargs['stderr'] == subprocess.DEVNULL,
            'SELF_TEST_RESOLVER_LAUNCH_BOUNDARY')
    with patch.object(subprocess, 'Popen', side_effect=Blocked('SELF_TEST_NO_EXEC')) as launch:
        try:
            resolver_query(contained_anchor, '@cfworker/json-schema', '/usr/bin', no_global=True)
        except Blocked as error:
            require(error.args == ('SELF_TEST_NO_EXEC',), 'SELF_TEST_CONTAINED_NO_EXEC')
    require(launch.call_args.args[0][1:3] == ['--no-global-search-paths', '--input-type=commonjs'],
            'SELF_TEST_NO_GLOBAL_FLAG')
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
    census_manifest = {'name': '@deepseek-ai/dsh',
                       'peerDependencies': {name: '*' for name in ('optional', 'required', 'unspecified', 'malformed')},
                       'peerDependenciesMeta': {'optional': {'optional': True}, 'required': {'optional': False},
                                                'malformed': {'optional': 'must not be emitted'}}}
    census_trust = SimpleNamespace(read=lambda _: json.dumps(census_manifest).encode(), resolve=missing_package, verify=lambda: None)
    census_stats = {}
    with patch.dict(globals(), {'KNOWN_MAPPINGS': {}}), \
         patch.object(subprocess, 'Popen', side_effect=AssertionError('census must not execute Node')):
        closure(census_trust, census_stats, census=True)
        records = census_stats['unresolved_edges']
        require([r['optional_classification'] for r in records] == ['TRUE', 'FALSE', 'MISSING', 'MALFORMED']
                and all(r['logical_anchor'] == PACKAGE + '/package.json' for r in records)
                and all(r['declaring_manifest_sha256'] == hashlib.sha256(json.dumps(census_manifest).encode()).hexdigest() for r in records)
                and 'must not be emitted' not in json.dumps(records), 'SELF_TEST_CENSUS_DECLARATIONS')
        census_manifest['peerDependencies'] = {f'missing{i}': '*' for i in range(33)}
        try:
            closure(census_trust, census_stats, census=True)
        except Blocked as error:
            require(error.args == ('CENSUS_UNRESOLVED_BOUND',) and len(census_stats['unresolved_edges']) == 32,
                    'SELF_TEST_CENSUS_BOUND')
        else:
            raise RuntimeError('unresolved census cap accepted')
        census_manifest['dependencies'] = []
        try:
            closure(census_trust, census_stats, census=True)
        except Blocked as error:
            require(error.args == ('DEPENDENCY_MAP',) and census_stats['census_context']['dependency_kind'] == 'dependencies',
                    'SELF_TEST_CENSUS_MALFORMED_CONTEXT')
        else:
            raise RuntimeError('malformed census declaration accepted')
    def exhausted(*unused):
        raise OSError(24, 'must never appear in output')
    fake = SimpleNamespace(held={'mock': (71, None, None)}, read=exhausted)
    for fail_restore, census_mode in ((False, False), (True, False), (False, True)):
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
            diagnostic = preflight_diagnostic(unresolved_census=census_mode)
        require(diagnostic['status'] == ('UNRESOLVED_CENSUS_INCOMPLETE' if census_mode else 'FD_LIMIT_RESTORE_FAILED' if fail_restore else 'DIAGNOSTIC_BLOCKED')
                and diagnostic['stage'] == 'SOURCE_PINS' and diagnostic['errno'] == 24
                and diagnostic['held_fd_count'] == 1 and diagnostic['last_successful_fd_count'] == 2,
                'SELF_TEST_DIAGNOSTIC_FAILURE')
        require(events == [('set', (4096, 1048576)), ('close', 71), ('set', (1024, 1048576))],
                'SELF_TEST_LIMIT_RESTORE_ORDER')
        require(diagnostic['fd_applied_hard_limit'] == diagnostic['fd_restored_hard_limit'] == 1048576
                and diagnostic['fd_restored_soft_limit'] == (4096 if fail_restore else 1024)
                and diagnostic['fd_restoration'] == ('FAILED' if fail_restore else 'PASS'), 'SELF_TEST_LIMIT_RESTORATION')
    with patch('builtins.open', return_value=io.StringIO('123\n456\n')) as group_file:
        require(group_pids('/system.slice/' + UNIT_V2, UNIT_V2) == {123, 456}, 'SELF_TEST_V2_REAL_CGROUP')
        group_file.assert_called_once_with('/sys/fs/cgroup/system.slice/' + UNIT_V2 + '/cgroup.procs', encoding='ascii')
    for group, target in (('/system.slice/' + UNIT, UNIT_V2), ('/system.slice/' + UNIT_V2, UNIT),
                          ('/system.slice/other.service', 'other.service')):
        with patch('builtins.open') as group_file:
            try:
                group_pids(group, target)
            except Blocked as error:
                require(error.args == ('CGROUP_PATH',) and not group_file.called, 'SELF_TEST_CROSS_UNIT_REJECTED')
            else:
                raise Blocked('SELF_TEST_CROSS_UNIT_ACCEPTED')
    with patch('builtins.open', return_value=io.StringIO('123\n')) as group_file:
        require(group_pids('/system.slice/' + UNIT_V3, UNIT_V3) == {123}, 'SELF_TEST_V3_REAL_CGROUP')
        group_file.assert_called_once_with('/sys/fs/cgroup/system.slice/' + UNIT_V3 + '/cgroup.procs', encoding='ascii')
    source_events = []
    source_fixture = SimpleNamespace(read=lambda path: source_events.append(('read', path)) or b'[Service]\nExecStart=/bin/true\n',
                                     verify=lambda: source_events.append(('verify',)), close=lambda: source_events.append(('close',)))
    def source_show(unit, keys):
        require(unit == UNIT_V3, 'SELF_TEST_V3_SOURCE_TARGET')
        source_events.append(('show',))
        return {'FragmentPath': '/run/systemd/transient/' + UNIT_V3, 'DropInPaths': '', 'PassEnvironment': ''}
    with patch.dict(globals(), {'Trusted': lambda: source_fixture, 'show': source_show}):
        envfile_absence_proof(UNIT_V3, sockets=True)
    require(source_events == [('show',), ('read', '/run/systemd/transient/' + UNIT_V3), ('verify',),
                              ('show',), ('verify',), ('close',)], 'SELF_TEST_V3_SOURCE_HELD_RECHECK')
    # Drive v2 through preflight, launch capture, early validation failure and owned cleanup.
    node, entry = '/opt/node-v24.19.0-linux-x64/bin/node', PACKAGE + '/lib/bin.js'
    pilot_fixture = ({'EnvironmentFiles': ''}, (829, 1, '/pilot', 'pilot-net'),
                     [node, entry, 'web', '--host', '127.0.0.1', '--port', '3080'], '/usr/bin')
    for runtime_target, wrong_owner, secondary in ((UNIT_V2, False, None), (UNIT_V3, False, None),
                                                    (UNIT_V3, True, None), (UNIT_V3, False, 'absence'),
                                                    (UNIT_V3, False, 'fd'), (UNIT_V3, False, 'socket')):
        controls, checks, description = [], [], ['']
        def fake_command(args, *unused, **kwargs):
            controls.append(args)
            if args[0] == '/usr/bin/systemd-run':
                description[0] = next(x.split('=', 1)[1] for x in args if x.startswith('--description='))
            return ''
        def fake_show(unit, keys):
            if unit == UNIT_V3.removesuffix('.service') + '.socket':
                require(keys == ['LoadState'], 'SELF_TEST_SOCKET_QUERY')
                return {'LoadState': 'loaded' if secondary == 'socket' else 'not-found'}
            require(unit == runtime_target, 'SELF_TEST_V2_UNIT')
            if keys == ['LoadState']:
                return {'LoadState': 'not-found'}
            if keys == ['LoadState', 'ActiveState']:
                return {'LoadState': 'loaded', 'ActiveState': 'inactive'}
            return {'InvocationID': 'a' * 32, 'Description': 'wrong' if wrong_owner else description[0],
                    'Transient': 'yes', 'ControlGroup': '/owned'}
        def fake_absence():
            checks.append('absence')
            require(not (secondary == 'absence' and len(controls) > 1), 'RESOLVER_ANCESTOR_EXISTS')
        fake_stat = SimpleNamespace(st_nlink=1, st_mode=0o100755)
        fake_trust = SimpleNamespace(held={'fixture': (71, None, None)}, open=lambda *a: 71,
                                    read=lambda path: ('#!/bin/sh\nexec ' + node + ' ' + entry + ' "$@"\n').encode()
                                    if path == '/usr/local/bin/dsh' else b'source',
                                    resolve=lambda path, **kw: path, verify=lambda: None,
                                    digest_runtime=lambda path: 'bc17c508ffeed0ec622934f9b7fa72f8e78da65350e63c3eceb56fa688aa5e12')
        def fake_closure(trust, stats, resolver, contained):
            require(contained is True and callable(resolver), 'SELF_TEST_V2_CONTAINED_REQUIRED')
            stats['contained_edge_count'] = 4
            return {}, {}
        with patch.dict(globals(), {'Trusted': lambda: fake_trust, 'SOURCE_PINS': {'/source': hashlib.sha256(b'source').hexdigest()},
                                   'KNOWN_MAPPINGS': {}, 'pilot_baseline': lambda: pilot_fixture, 'listeners': lambda _: [],
                                   'candidate_inventory': lambda *args: {}, 'closure': fake_closure, 'show': fake_show,
                                   'command': fake_command, 'snapshot': lambda _: 1, 'group_pids': lambda group, target: [],
                                   'absent_resolver_ancestors': lambda _: fake_absence,
                                   'effective_properties': lambda _: require(False, 'UNIT_PROPERTIES_MISSING')}), \
             patch.object(sys, 'platform', 'linux'), patch.object(sys, 'version_info', (3, 12)), \
             patch.object(socket, 'gethostname', return_value='deepseek-harness-01'), \
             patch.object(os, 'geteuid', return_value=0, create=True), patch.object(os, 'getegid', return_value=0, create=True), \
             patch.object(os, 'fstat', return_value=fake_stat), patch.object(os, 'lstat', return_value=fake_stat), \
             patch.object(os, 'stat', return_value=fake_stat), patch.object(os, 'readlink', return_value='pilot-net'), \
             patch.object(os.path, 'lexists', return_value=False), \
             patch.object(os, 'close', side_effect=OSError(9, 'private error') if secondary == 'fd' else None) as closed:
            runtime = apply(v2=True, target=runtime_target) if runtime_target == UNIT_V3 else apply(v2=True)
        if secondary == 'socket':
            require(not controls and runtime['primary_error_code'] == 'SOCKET_UNIT_EXISTS'
                    and runtime['status'] == 'BLOCKED', 'SELF_TEST_SOCKET_NO_START')
            continue
        if runtime_target == UNIT_V3:
            require(runtime['primary_error_code'] == ('UNIT_OWNERSHIP' if wrong_owner else 'UNIT_PROPERTIES_MISSING')
                    and runtime['cleanup_error_code'] == ('CLEANUP_OWNERSHIP' if wrong_owner else 'HELD_NAMESPACE_UNAVAILABLE'),
                    'SELF_TEST_PRIMARY_CLEANUP_RETAINED')
        require(controls[0][-9:] == [node, '--no-global-search-paths', entry, 'web', '--host', '127.0.0.1', '--port', '3081', '--no-open'],
                'SELF_TEST_V2_DIRECT_ARGV')
        require(runtime['status'] == 'CLEANUP_NOT_PROVEN' and len(checks) >= 3 and closed.call_count == 1,
                'SELF_TEST_V2_EARLY_CLEANUP')
        require((len(controls) == 1 if wrong_owner else controls[-1] == ['/usr/bin/systemctl', 'stop', runtime_target])
                and ('OWNED_PROCESS_CLEANUP_PASS' in runtime['checkpoints']) is (not wrong_owner)
                and 'OWNED_CLEANUP_PASS' not in runtime['checkpoints'], 'SELF_TEST_V2_CLEANUP_OWNERSHIP')
    for runtime_target, restore_failure in ((UNIT_V2, False), (UNIT_V2, True), (UNIT_V3, False), (UNIT_V3, True)):
        limits, events = [1024, 1048576], []
        def v2_limits(_, values):
            events.append(tuple(values))
            if not (restore_failure and values[0] == 1024):
                limits[:] = values
        def v2_inner(v2, target=None):
            require(v2 is True and limits == [4096, 1048576], 'SELF_TEST_V2_LIMIT_APPLIED')
            events.append('owned_fds_closed')
            require(target == (UNIT_V3 if runtime_target == UNIT_V3 else None), 'SELF_TEST_LIMIT_TARGET')
            return {'status': 'CLEANUP_NOT_PROVEN', 'primary_error_code': 'UNIT_PROPERTIES_MISSING',
                    'cleanup_error_code': 'HELD_NAMESPACE_UNAVAILABLE'} if target == UNIT_V3 else {'status': 'BLOCKED'}
        with patch.dict(sys.modules, {'resource': SimpleNamespace(RLIMIT_NOFILE=7, getrlimit=lambda _: tuple(limits), setrlimit=v2_limits)}), \
             patch.dict(globals(), {'apply': v2_inner}):
            limit_result = apply_v2(runtime_target)
        require(events == [(4096, 1048576), 'owned_fds_closed', (1024, 1048576)]
                and limit_result['fd_restoration'] == ('FAILED' if restore_failure else 'PASS'), 'SELF_TEST_V2_LIMIT_RESTORE')
    require(limit_result['status'] == 'CLEANUP_NOT_PROVEN' and limit_result['primary_error_code'] == 'UNIT_PROPERTIES_MISSING'
            and limit_result['cleanup_error_code'] == 'HELD_NAMESPACE_UNAVAILABLE', 'SELF_TEST_RESTORE_PRIMARY_PRECEDENCE')
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
        lambda: resolver_output(b'null'),
        lambda: resolver_output(b'["relative"]'),
        lambda: resolver_output(b'["/a/../b"]'),
        lambda: resolver_output(json.dumps(['/root/' + str(i) for i in range(65)]).encode()),
        lambda: resolver_output(b' ' * 16385),
        lambda: contained_resolver_paths(contained_anchor, six_paths + ['/home/dsh/.node_modules']),
        lambda: contained_resolver_paths(contained_anchor, list(reversed(six_paths))),
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
    modes.add_argument('--apply-v2', action='store_true')
    modes.add_argument('--apply-v3', action='store_true')
    modes.add_argument('--attempt-journal-diagnostic', action='store_true')
    modes.add_argument('--socket-source-diagnostic', action='store_true')
    modes.add_argument('--self-test', action='store_true')
    modes.add_argument('--preflight-diagnostic', action='store_true')
    modes.add_argument('--resolver-diagnostic', action='store_true')
    modes.add_argument('--contained-preflight-diagnostic', action='store_true')
    modes.add_argument('--unresolved-census', action='store_true')
    args = parser.parse_args()
    try:
        result = (self_test() if args.self_test else socket_source_diagnostic() if args.socket_source_diagnostic else attempt_journal_diagnostic() if args.attempt_journal_diagnostic else preflight_diagnostic(unresolved_census=True) if args.unresolved_census
                  else preflight_diagnostic(contained_diagnostic=True) if args.contained_preflight_diagnostic
                  else preflight_diagnostic(resolver_diagnostic=True) if args.resolver_diagnostic
                  else preflight_diagnostic() if args.preflight_diagnostic else apply_v2(UNIT_V3) if args.apply_v3 else apply_v2() if args.apply_v2 else apply() if args.apply else {
            'status': 'CONTRACT_ONLY', 'runtime': 'NOT PROVEN', 'unit': UNIT,
            'candidate': HOME, 'properties': PROPERTIES, 'attempts': 1,
            'required_parent_checks': ['fresh source receipts', 'pilot loopback HTTP before/after', 'tunnel before/after'],
        })
    except Exception:
        result = {'status': 'BLOCKED', 'error_code': 'PRECONDITION_OR_SELF_TEST_FAILURE'}
    print(json.dumps(result, sort_keys=True))
    sys.exit(0 if result['status'] in {'SOCKET_SOURCE_DIAGNOSTIC_PASS', 'ATTEMPT_JOURNAL_COMPLETE', 'CONTRACT_ONLY', 'SELF_TEST_PASS', 'ISOLATED_CANDIDATE_SMOKE_PASS', 'READ_ONLY_PREFLIGHT_PASS', 'UNRESOLVED_CENSUS_COMPLETE'} else 1)
