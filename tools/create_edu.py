#!/usr/bin/env python3

import argparse
import os
import copy
import uuid
import yaml

argparser = argparse.ArgumentParser(description='Create eDU manifests')
argparser.add_argument('--destdir', '-d', required=True,
                       help='Directory to output eDU manifests')
argparser.add_argument('--image', '-i', required=False,
                       default='quay.io/cdonato/spammer:latest',
                       help='Container image to substitute in eDU manifests')
argparser.add_argument('--prefix', '-p', required=False,
                       default='edu',
                       help='Prefix to prepend to all resources')
args = argparser.parse_args()

maps = {'configmap':  {'iterator': 0, 'resources': {}},
        'container':  {'iterator': 0, 'resources': {}},
        'deployment': {'iterator': 0, 'resources': {}},
        'namespace':  {'iterator': 0, 'resources': {}},
        'pvc':        {'iterator': 0, 'resources': {}},
        'secret':     {'iterator': 0, 'resources': {}},
        'volume':     {'iterator': 0, 'resources': {}}}

resources = {'configmap':  [],
             'namespace':  [],
             'deployment': [],
             'pvc':        [],
             'secret':     []}

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
                   'pod-security.kubernetes.io/audit':   'privileged',
                   'pod-security.kubernetes.io/warn':    'privileged'}}},
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
  if(resourcename not in maps[resourcetype]['resources']):
    maps[resourcetype]['resources'][resourcename] = '-'.join([args.prefix, resourcetype,
                                                              str(maps[resourcetype]['iterator'])])
    maps[resourcetype]['iterator'] += 1
  return maps[resourcetype]['resources'][resourcename]


deployments = 1

volumes = [
           {"name":"volume-1",  "persistentVolumeClaim": 1},
           {"name":"volume-2", "secret": 1},
           {"name":"volume-3", "configMap":1}
           ]

containers = [
              # {"name": "container2", "memory": "1Gi", 
              #  "volumeMounts": [{"name":"volume-2"}],
              #  "livenessProbe": {"exec":{"command":"ls"},
              #                    "failureThreshold": 3,"initialDelaySeconds": 5,
              #                    "periodSeconds": 15,"successThreshold": 1,
              #                    "timeoutSeconds": 1},
              #  "readinessProbe": {"exec":{"command":"ls"}, 
              #                     "failureThreshold": 3,"periodSeconds": 5, 
              #                     "successThreshold": 1,"timeoutSeconds": 1}},
               {"name": "container1", "memory": "1024", 
               "volumeMounts": [{"name":"volume-1"}]}
              ]
               
# Create namespace
namespaceref = resourceref('namespace', 'default-namespace')
newnamespace = copy.deepcopy(templates['namespace'])
newnamespace['metadata']['name'] = namespaceref
resources['namespace'].append(newnamespace)

for i in range(deployments):

  deploymentref = resourceref('deployment', 'deployment-'+str(i))
  newdeployment = copy.deepcopy(templates['deployment'])
  newdeployment['metadata'] = {'name': deploymentref, 'namespace': namespaceref, 
                               'labels': {'app': deploymentref}}
  newdeployment['spec']['template']['metadata']['labels'] = {'app': deploymentref}
  newdeployment['spec']['selector']['matchLabels'] = {'app': deploymentref}

  for volume in volumes:
    volumeref = resourceref('volume', volume['name'])
    newvolume = copy.deepcopy(templates['volume'])
    newvolume['name'] = volumeref

    if 'configMap' in volume:
      for i in range(volume['configMap']):
        configmapref = resourceref('configmap', 'configMap-'+str(i))
        newconfigmap = copy.deepcopy(templates['configmap'])
        newconfigmap['metadata']['name'] = configmapref
        newconfigmap['metadata']['namespace'] = namespaceref
        resources['configmap'].append(newconfigmap)

        newvolume['configMap'] = {'name': configmapref}

    elif 'secret' in volume:
      for i in range(volume['secret']):
        secretref = resourceref('secret', 'secret-'+str(i))
        newsecret = copy.deepcopy(templates['secret'])
        newsecret['metadata']['name'] = secretref
        newsecret['metadata']['namespace'] = namespaceref
        resources['secret'].append(newsecret)

        newvolume['secret'] = {'secretName': secretref}

    elif 'persistentVolumeClaim' in volume:
      for i in range(volume['persistentVolumeClaim']):
        pvcref = resourceref('pvc', 'persistentVolumeClaim'+str(i))
        newpvc = copy.deepcopy(templates['pvc'])
        newpvc['metadata']['name'] = pvcref
        newpvc['metadata']['namespace'] = namespaceref
        resources['pvc'].append(newpvc)

        newvolume['persistentVolumeClaim'] = {'claimName': pvcref}
    
    elif 'emptyDir' in volume:
      newvolume['emptyDir'] = volume['emptyDir']

    newdeployment['spec']['template']['spec']['volumes'].append(newvolume)

  for container in containers:
    containerref = resourceref('container', '_'.join(['default', container['name']]))
    newcontainer = copy.deepcopy(templates['container'])
    newcontainer['name'] = containerref
    newcontainer['imagePullPolicy'] = 'Always'
    newcontainer['env'] = [
      {'name': 'NUM_THREADS', 'value': '{{ spammer_num_threads["' + containerref 
       + '"] | default(spammer_num_threads_default) }}'},
      {'name': 'PER_CPU', 'value': '{{ spammer_per_cpu["' + containerref
       + '"] | default(spammer_per_cpu_default) }}'},
      {'name': 'MAX_MEM', 'value': container['memory']},
      {'name': 'PER_MEM', 'value': '{{ spammer_per_mem["' + containerref 
       + '"] | default(spammer_per_mem_default) }}'}]
      
    for property in ['ports', 'resources', 'securityContext']:
      if property in container:
        newcontainer[property] = container[property]

    for property in ['livenessProbe', 'readinessProbe', 'startupProbe']:
      if property in container:
        newcontainer[property] = container[property]

        if 'exec' in newcontainer[property]:
            newcontainer[property]['exec']['command'] = ['ls']
        elif 'httpGet' in newcontainer[property] and not list(filter(lambda x: (x['name'] == "LISTEN_PORT"), newcontainer['env'])):
          newcontainer['env'].append({'name': 'LISTEN_PORT', 'value': str(newcontainer[property]['httpGet']['port'])})
          newcontainer['env'].append({'name': 'LISTEN', 'value': '1'})
        elif 'tcpSocket' in newcontainer[property] and not list(filter(lambda x: (x['name'] == "LISTEN_PORT"), newcontainer['env'])):
          newcontainer['env'].append({'name': 'LISTEN_PORT', 'value': str(newcontainer[property]['tcpSocket']['port'])})

    for volumemount in container['volumeMounts']:
      volumeref = resourceref('volume', volumemount['name'])
      mountpath = "/tmp/" + str(uuid.uuid4())
      newvolumemount = {'mountPath': mountpath, 'name': volumeref}

      if 'readOnly' in volumemount and volumemount['readOnly'] == True:
        newvolumemount['readOnly'] = True

      newcontainer['volumeMounts'].append(newvolumemount)
    
    newdeployment['spec']['template']['spec']['containers'].append(newcontainer)

  resources['deployment'].append(newdeployment)

print(resources)
if not os.path.isdir(args.destdir):
  os.mkdir(args.destdir)

for resourcetype in resources.keys():
  yamlout = open(os.path.join(args.destdir, resourcetype + ".yaml"), "w")
  yaml.dump_all(resources[resourcetype], yamlout, default_flow_style=False, width=1000)
  yamlout.close()

# ansible role expects j2..? Yes it replaces spammer envs
os.rename(os.path.join(args.destdir,"deployment.yaml"),os.path.join(args.destdir,"deployment.yaml.j2"))
