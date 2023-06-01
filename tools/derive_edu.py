#!/usr/bin/env python3

import yaml
import argparse
import os
import re
import copy
import uuid

argparser = argparse.ArgumentParser(description='Derive eDU manifests from YAML pod specs')
argparser.add_argument('--destdir', '-d', required=True, help='Directory to output eDU manifests')
argparser.add_argument('--image', '-i', required=False, default='quay.io/cdonato/spammer:latest', help='Container image to substitute in eDU manifests')
argparser.add_argument('--prefix', '-p', required=False, default='edu', help='Prefix to prepend to all resources')
argparser.add_argument('--sourcedir', '-s', required=True, help='Directory containing YAML pod specs')
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
                     'storage': '10Gi'}},
                 'storageClassName': 'local-sc'}},
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
    maps[resourcetype]['resources'][resourcename] = '-'.join([args.prefix, resourcetype, str(maps[resourcetype]['iterator'])])
    maps[resourcetype]['iterator'] += 1

  return maps[resourcetype]['resources'][resourcename]

def mem_in_mb(memrequest):
  rematch = re.match('(\d+)(\D+)', memrequest)
  memamount = int(rematch.group(1))
  memunit = rematch.group(2)

  if re.match('[Gg][Ii]', memunit):
    memamount = memamount * 1024

  return memamount


for sourcefile in os.listdir(args.sourcedir):
  if not (re.match('.*.yaml', sourcefile) and os.path.isfile(os.path.join(args.sourcedir, sourcefile))):
    continue

  yamlin = open(os.path.join(args.sourcedir, sourcefile), 'r')
  yamldata = yaml.load(yamlin)
  yamlin.close()

  namespaceref = resourceref('namespace', yamldata['metadata']['namespace'])

  if not list(filter(lambda x: (x['metadata']['name'] == namespaceref), resources['namespace'])):
    newnamespace = copy.deepcopy(templates['namespace'])
    newnamespace['metadata']['name'] = namespaceref
    resources['namespace'].append(newnamespace)

  deploymentref = resourceref('deployment', yamldata['metadata']['name'])

  if not list(filter(lambda x: (x['metadata']['name'] == deploymentref), resources['deployment'])):
    newdeployment = copy.deepcopy(templates['deployment'])
    newdeployment['metadata'] = {'name': deploymentref, 'namespace': namespaceref, 'labels': {'app': deploymentref}}
    newdeployment['spec']['template']['metadata']['labels'] = {'app': deploymentref}
    newdeployment['spec']['selector']['matchLabels'] = {'app': deploymentref}
  
    for volume in yamldata['spec']['volumes']:
      volumeref = resourceref('volume', volume['name'])
      newvolume = copy.deepcopy(templates['volume'])
      newvolume['name'] = volumeref

      if 'configMap' in volume:
        configmapref = resourceref('configmap', volume['configMap']['name'])

        if not list(filter(lambda x: (x['metadata']['name'] == configmapref), resources['configmap'])):
          newconfigmap = copy.deepcopy(templates['configmap'])
          newconfigmap['metadata']['name'] = configmapref
          newconfigmap['metadata']['namespace'] = namespaceref
          resources['configmap'].append(newconfigmap)

        newvolume['configMap'] = {'name': configmapref}

      elif 'secret' in volume:
        secretref = resourceref('secret', volume['secret']['secretName'])

        if not list(filter(lambda x: (x['metadata']['name'] == secretref), resources['secret'])):
          newsecret = copy.deepcopy(templates['secret'])
          newsecret['metadata']['name'] = secretref
          newsecret['metadata']['namespace'] = namespaceref
          resources['secret'].append(newsecret)

        newvolume['secret'] = {'secretName': secretref}

      elif 'persistentVolumeClaim' in volume:
        pvcref = resourceref('pvc', volume['persistentVolumeClaim']['claimName'])

        if not list(filter(lambda x: (x['metadata']['name'] == pvcref), resources['pvc'])):
          newpvc = copy.deepcopy(templates['pvc'])
          newpvc['metadata']['name'] = pvcref
          newpvc['metadata']['namespace'] = namespaceref
          resources['pvc'].append(newpvc)

        newvolume['persistentVolumeClaim'] = {'claimName': pvcref}

      elif 'emptyDir' in volume:
        newvolume['emptyDir'] = volume['emptyDir']

      newdeployment['spec']['template']['spec']['volumes'].append(newvolume)

    for container in yamldata['spec']['containers']:
      containerref = resourceref('container', '_'.join([yamldata['metadata']['name'], container['name']]))
      newcontainer = copy.deepcopy(templates['container'])
      newcontainer['name'] = containerref
      newcontainer['imagePullPolicy'] = 'Always'
      newcontainer['env'] = [
        {'name': 'NUM_THREADS', 'value': '{{ spammer_num_threads["' + containerref + '"] | default(spammer_num_threads_default) }}'},
        {'name': 'PER_CPU', 'value': '{{ spammer_per_cpu["' + containerref + '"] | default(spammer_per_cpu_default) }}'},
        {'name': 'MAX_MEM', 'value': str(mem_in_mb(container['resources']['requests']['memory']))},
        {'name': 'PER_MEM', 'value': '{{ spammer_per_mem["' + containerref + '"] | default(spammer_per_mem_default) }}'}]

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
            newcontainer['env'].append({'name': 'LISTEN', 'value': '1'})

      for volumemount in container['volumeMounts']:
        volumeref = resourceref('volume', volumemount['name'])
        mountpath = "/tmp/" + str(uuid.uuid4())
        newvolumemount = {'mountPath': mountpath, 'name': volumeref}

        if 'readOnly' in volumemount and volumemount['readOnly'] == True:
          newvolumemount['readOnly'] = True

        newcontainer['volumeMounts'].append(newvolumemount)

      newdeployment['spec']['template']['spec']['containers'].append(newcontainer)

    resources['deployment'].append(newdeployment)

if not os.path.isdir(args.destdir):
  os.mkdir(args.destdir)

for resourcetype in resources.keys():
  yamlout = open(os.path.join(args.destdir, resourcetype + ".yaml"), "w")
  yaml.dump_all(resources[resourcetype], yamlout, default_flow_style=False, width=1000)
  yamlout.close()
