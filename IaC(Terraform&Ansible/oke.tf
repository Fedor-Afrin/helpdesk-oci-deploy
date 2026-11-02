

data "oci_core_images" "oracle_linux_amd_standard" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.E4.Flex"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_containerengine_cluster" "k8s_cluster" {
  compartment_id = var.compartment_ocid
  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.oke_api_endpoint_subnet.id
  }
  kubernetes_version = var.k8s_version
  name               = var.oke_cluster_name
  vcn_id             = oci_core_vcn.vcn.id
  type               = "BASIC_CLUSTER"
}

resource "oci_containerengine_node_pool" "k8s_node_pool" {
  cluster_id         = oci_containerengine_cluster.k8s_cluster.id
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.k8s_version
  name               = "amd-standard-pool"

  node_config_details {
    placement_configs {
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      subnet_id           = oci_core_subnet.oke_nodes_subnet.id
    }
    size = 1
  }

  node_shape = "VM.Standard.E4.Flex"

  node_shape_config {
    memory_in_gbs = 8
    ocpus         = 1
  }

  node_source_details {
    image_id    = data.oci_core_images.oracle_linux_amd_standard.images[0].id
    source_type = "IMAGE"
  }

  ssh_public_key = var.ssh_public_key
}
