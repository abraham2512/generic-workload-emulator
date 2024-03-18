#!/usr/bin/env python3

import argparse
import os
import copy
import uuid
import yaml
from os import listdir
import shutil
from jinja2 import Environment, FileSystemLoader

argparser = argparse.ArgumentParser(description='Create eDU manifests')
argparser.add_argument('--destdir', '-d', required=False,
                       help='Directory to output eDU manifests',
                       default='automation/roles/setup_edu/files')
argparser.add_argument('--image', '-i', required=False,
                       default='ghcr.io/abraham2512/fedora-stress-ng:master',
                       help='Container image to substitute in eDU manifests')
argparser.add_argument('--prefix', '-p', required=False,
                       default='edu',
                       help='Prefix to prepend to all resources')
argparser.add_argument('--config', '-c', required=False,
                       default='tools/configs.yaml',
                       help='Config yaml with pod specs')
args = argparser.parse_args()

maps = {'configmap': {'iterator': 0, 'resources': {}},
        'container': {'iterator': 0, 'resources': {}},
        'deployment': {'iterator': 0, 'resources': {}},
        'namespace': {'iterator': 0, 'resources': {}},
        # 'pvc': {'iterator': 0, 'resources': {}},
        'secret': {'iterator': 0, 'resources': {}},
        'volume': {'iterator': 0, 'resources': {}}}

resources = {'configmap': [],
             'namespace': [],
             'deployment': [],
            #  'pvc': [],
             'secret': []}

templates = {'configmap': {
    'apiVersion': 'v1',
    'kind': 'ConfigMap',
    'metadata': {
        'name': '',
        'namespace': ''},
    'data': {
        'property1': 'value1',
        'property2': 'value2',
        'property3': 'value3'}},
    'container': {
    'name': '',
    'image': args.image,
    'imagePullPolicy': 'IfNotPresent',
    'env': [],
    'volumeMounts': []},
    'deployment': {
    'apiVersion': 'apps/v1',
    'kind': 'Deployment',
    'metadata': {
        'name': '',
        'namespace': '',
        'labels': {
            'app': 'test1'}},
    'spec': {
        'replicas': 1,
        'selector': {
            'matchLabels': {
                'app': ''}},
        'template': {
            'metadata': {
                'labels': {
                    'app': 'test1'}},
            'spec': {
                'containers': [],
                'volumes': []}}}},
    'namespace': {
    'apiVersion': 'v1',
    'kind': 'Namespace',
    'metadata': {
        'name': '',
        'labels': {
            'pod-security.kubernetes.io/enforce': 'privileged',
            'pod-security.kubernetes.io/audit': 'privileged',
            'pod-security.kubernetes.io/warn': 'privileged'}}},
    'pvc': {
    'kind': 'PersistentVolumeClaim',
    'apiVersion': 'v1',
    'metadata': {
        'name': '',
        'namespace': ''},
    'spec': {
        'accessModes': ['ReadWriteOnce'],
        'volumeMode': 'Filesystem',
        'resources': {
            'requests': {
                'storage': '1Gi'}},
        'storageClassName': 'general'}},
    'secret': {
    'apiVersion': 'v1',
    'kind': 'Secret',
    'metadata': {
        'name': '',
        'namespace': ''},
    'type': 'Opaque',
    'data': {
        'secret1': 'YmxhaGJsYWgK',
                   'secret2': 'ZXRjZXRjCg==',
                   'secret3': 'eWFkYXlhZGEK'}},
    'volume': {
    'name': ''}}


def resourceref(resourcetype, resourcename):
    if (resourcename not in maps[resourcetype]['resources']):
        maps[resourcetype]['resources'][resourcename] = '-'.join([args.prefix, resourcetype,
                                                                  str(maps[resourcetype]['iterator'])])
        maps[resourcetype]['iterator'] += 1
    return maps[resourcetype]['resources'][resourcename]


du_specs = None
with open(args.config, "r") as fstream:
    du_specs = yaml.safe_load(fstream)
# print(du_specs)

deployments = du_specs['deployments']
d = 0

# Create namespace
namespaceref = resourceref('namespace', 'default-namespace')
newnamespace = copy.deepcopy(templates['namespace'])
newnamespace['metadata']['name'] = namespaceref
resources['namespace'].append(newnamespace)

for deployment in deployments:
    d += 1
    deploymentref = resourceref('deployment', 'deployment-' + str(d))
    newdeployment = copy.deepcopy(templates['deployment'])
    newdeployment['metadata'] = {'name': deploymentref, 'namespace': namespaceref,
                                 'labels': {'app': deploymentref}}
    newdeployment['spec']['template']['metadata']['labels'] = {
        'app': deploymentref}
    newdeployment['spec']['selector']['matchLabels'] = {'app': deploymentref}

    volumes = deployment.get('volumes', None)
    pods = deployment.get('pods', None)
    containers = []
    for pod in pods:
        n = pod.pop('name')
        r = pod.pop('repeat')
        for i in range(r):
            newcontainer = {}
            newcontainer = copy.deepcopy(pod)
            newcontainer['name'] = '_'.join([n, str(i)])
            containers.append(newcontainer)
    if volumes:
        for volume in volumes:
            volumeref = resourceref('volume', volume['name'])
            newvolume = copy.deepcopy(templates['volume'])
            newvolume['name'] = volumeref

            if 'configMap' in volume:
                for i in range(volume['configMap']):
                    configmapref = resourceref(
                        'configmap', 'configMap-' + str(i))
                    newconfigmap = copy.deepcopy(templates['configmap'])
                    newconfigmap['metadata']['name'] = configmapref
                    newconfigmap['metadata']['namespace'] = namespaceref
                    resources['configmap'].append(newconfigmap)

                    newvolume['configMap'] = {'name': configmapref}

            elif 'secret' in volume:
                for i in range(volume['secret']):
                    secretref = resourceref('secret', 'secret-' + str(i))
                    newsecret = copy.deepcopy(templates['secret'])
                    newsecret['metadata']['name'] = secretref
                    newsecret['metadata']['namespace'] = namespaceref
                    resources['secret'].append(newsecret)

                    newvolume['secret'] = {'secretName': secretref}

            elif 'persistentVolumeClaim' in volume:
                for i in range(volume['persistentVolumeClaim']):
                    pvcref = resourceref(
                        'pvc', 'persistentVolumeClaim' + str(i))
                    newpvc = copy.deepcopy(templates['pvc'])
                    newpvc['metadata']['name'] = pvcref
                    newpvc['metadata']['namespace'] = namespaceref
                    resources['pvc'].append(newpvc)

                    newvolume['persistentVolumeClaim'] = {'claimName': pvcref}

            elif 'emptyDir' in volume:
                newvolume['emptyDir'] = volume['emptyDir']

            newdeployment['spec']['template']['spec']['volumes'].append(
                newvolume)
    if containers:
        for container in containers:
            containerref = resourceref(
                'container', '_'.join(['default', container['name']]))
            newcontainer = copy.deepcopy(templates['container'])
            newcontainer['name'] = containerref
            newcontainer['imagePullPolicy'] = 'Always'
            newcontainer['env'] = container['env']

            for property in ['ports', 'resources', 'securityContext']:
                if property in container:
                    newcontainer[property] = container[property]

            for property in ['livenessProbe',
                             'readinessProbe', 'startupProbe']:
                if property in container:
                    newcontainer[property] = container[property]

                    if 'exec' in newcontainer[property]:
                        newcontainer[property]['exec']['command'] = ['ls']
                    elif 'httpGet' in newcontainer[property] and not list(filter(lambda x: (x['name'] == "LISTEN_PORT"), newcontainer['env'])):
                        newcontainer['env'].append({'name': 'LISTEN_PORT', 'value': str(
                            newcontainer[property]['httpGet']['port'])})
                        newcontainer['env'].append(
                            {'name': 'LISTEN', 'value': '1'})
                    elif 'tcpSocket' in newcontainer[property] and not list(filter(lambda x: (x['name'] == "LISTEN_PORT"), newcontainer['env'])):
                        newcontainer['env'].append({'name': 'LISTEN_PORT', 'value': str(
                            newcontainer[property]['tcpSocket']['port'])})

            if 'volumeMounts' in container.keys():
                for volumemount in container['volumeMounts']:
                    volumeref = resourceref('volume', volumemount['name'])
                    mountpath = "/tmp/" + str(uuid.uuid4())
                    newvolumemount = {
                        'mountPath': mountpath, 'name': volumeref}

                    if 'readOnly' in volumemount and volumemount['readOnly'] == True:
                        newvolumemount['readOnly'] = True

                    newcontainer['volumeMounts'].append(newvolumemount)

            newdeployment['spec']['template']['spec']['containers'].append(
                newcontainer)

    resources['deployment'].append(newdeployment)

print(resources['deployment'])
if not os.path.isdir(args.destdir):
    os.mkdir(args.destdir)

for resourcetype in resources.keys():
    yamlout = open(os.path.join(args.destdir, resourcetype + ".yaml"), "w")
    yaml.dump_all(
        resources[resourcetype],
        yamlout,
        default_flow_style=False,
        width=1000)
    yamlout.close()


def generate_test_files(image_registry):
    TEMPLATE_DIR = args.destdir+'/templates/'
    TEMPLATE_SRC = 'tools/templates/'

    if os.path.isdir(TEMPLATE_DIR):
        shutil.rmtree(TEMPLATE_DIR)
        print(f"Directory '{TEMPLATE_DIR}' has been deleted.")

    shutil.copytree(TEMPLATE_SRC, TEMPLATE_DIR)
    print(f"Directory '{TEMPLATE_SRC}' has been copied.")

    template_filenames = listdir(TEMPLATE_DIR)
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    try:
        fec_accelerator = os.environ["FEC_ACCELERATOR"]
    except KeyError:
        fec_accelerator = 'none'

    for template_file in template_filenames:
        template = env.get_template(template_file)

        content = template.render(registry_address=image_registry,
                                  accelerator=fec_accelerator)

        with open(TEMPLATE_DIR+template_file, mode='w', encoding='utf-8') as rendered_file:
            rendered_file.write(content)


generate_test_files('registry.testsno.com')

SECRETS_DIR = args.destdir+'/secrets/'
SECRETS_SRC = 'tools/secrets'

if os.path.isdir(SECRETS_DIR):
    shutil.rmtree(SECRETS_DIR)
    print(f"Directory '{SECRETS_DIR}' has been deleted.")

shutil.copytree(SECRETS_SRC, SECRETS_DIR)
print(f"Directory '{SECRETS_SRC}' has been copied.")

footprint_files = ['tools/pv.yaml', 'tools/pv1.yaml', 'tools/pv2.yaml',
                   'tools/pvc.yaml', 'tools/security.yaml',
                   'tools/test-ns.yaml', 'tools/sriov-networks.yaml']

[shutil.copy(file, args.destdir) for file in footprint_files]