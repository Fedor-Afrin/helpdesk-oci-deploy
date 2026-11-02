output "kubeconfig_command" {
  value = "oci ce cluster create-kubeconfig --cluster-id ${oci_containerengine_cluster.k8s_cluster.id} --file $HOME/.kube/config --region ${var.region} --token-version 2.0.0 --kube-endpoint PUBLIC_ENDPOINT"
}

output "public_subnet_ocid" {
  value = oci_core_subnet.oke_nodes_subnet.id
}

output "cluster_id" {
  value = oci_containerengine_cluster.k8s_cluster.id
}

output "region" {
  value = var.region
}
