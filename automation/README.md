# Automation

The automation directory contains Ansible tooling to automate deployment of the eDU. The playbooks are simple wrappers around the roles, use whichever is more appropriate for your use case.

## Inventory

Create an `automation/inventory` file with the following format:

```
cluster ansible_hostname=$HOSTNAME remote_user=$USER kubeconfig_path=$KUBECONFIG
```

For example:

```
cluster ansible_hostname=cluster.snocluster123.example.com remote_user=core kubeconfig_path=~/.kube/kubeconfig_snocluster123
```

Note that the Ansible controller will need to be able to SSH to the node for the partition creation.

## Partitions

The eDU requires 26x10 Gi partitions on the host machine, as specified in the [setup_lvs role](automation/roles/setup_lvs/defaults/main.yml`). These are not being created using a `MachineConfig` in order to avoid a cluster restart. Note that these partitions will persist across redeploys of the cluster so it is only needed once per node.

Create partitions on the target cluster using the `create_partitions` playbook:

```shell
ansible-playbook playbooks/create_partitions.yml -i inventory
```

This will SSH into the machine and create the required LVs

## eDU deployment

To setup the eDU use the `setup_edu` playbook (or role).

```shell
ansible-playbook playbooks/setup_edu.yml -i inventory
```

Optional extra-vars are as follows:

- **debug_mode** (default: false)

  enable debug messages

- **setup_edu_ansible_verification** (default: true)

  wait for pods to become ready before completing 

- **spammer_per_mem_default** (default: 50)

  percentage of requested memory that the spammer image will consume per container

- **spammer_num_threads_default** (default: 4)

  number of threads that the spammer image will spin up per container

- **spammer_per_cpu_default** (default: 2)

  number of calculations between injecting sleep in order to control CPU usage

For example:
```shell
ansible-playbook playbooks/setup_edu.yml -i inventory -e setup_edu_ansible_verification=false -e spammer_per_mem_default=25 -e spammer_num_threads_default=2
```

Additionally, the spammer_per_mem, spammer_num_threads, and spammer_per_cpu values can be tuned to override default settings per container for fine-grained control, for example:

```shell
ansible-playbook playbooks/setup_edu.yml -i inventory -e '{"spammer_per_mem": {"edu-container-0": 75, "edu-container-42": 10}, "spammer_num_threads": {"edu-container-99": 2}, "spammer_per_cpu": {"edu-container-22": 5}}'
```

Depending on the degree of cutomization, it may be preferable to define these vars in inventory, for example:

```shell
$ cat automation/host_vars/cluster.yml
spammer_per_mem:
  edu-container-0: 75
  edu-container-42: 10
spammer_num_threads:
  edu-container-99: 2
spammer_per_cpu:
  edu-container-22: 5
```

## eDU Teardown

To remove the eDU from a cluster, use the `teardown_edu` playbook (or role).

```shell
ansible-playbook playbooks/teardown_edu.yml -i inventory
```

There is the option to remove only the pods, leaving the namespace and persistent volumes in place for testing purposes, using the `remove_pods_only` variable. By default the entire namespace will be removed, including the persistent volumes. For example, to leave the PVs:

```shell
ansible-playbook playbooks/teardown_edu.yml -i inventory -e remove_pods_only=true
```
