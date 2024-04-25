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


Create partitions on the target cluster using the `create_partitions` playbook:

```shell
ansible-playbook playbooks/create_partitions.yml -i inventory
```

This will SSH into the machine and create the required LVs

## eDU deployment

To setup the eDU use the `setup_edu` playbook (or role).


For example:
```shell
ansible-playbook playbooks/setup_edu.yml -i inventory -r registry
```


## eDU Teardown

To remove the eDU from a cluster, use the `teardown_edu` playbook (or role).

```shell
ansible-playbook playbooks/teardown_edu.yml -i inventoy
```

There is the option to remove only the pods, leaving the namespace and persistent volumes in place for testing purposes, using the `remove_pods_only` variable. By default the entire namespace will be removed, including the persistent volumes. For example, to leave the PVs:

```shell
ansible-playbook playbooks/teardown_edu.yml -i inventory -e remove_pods_only=true
```
