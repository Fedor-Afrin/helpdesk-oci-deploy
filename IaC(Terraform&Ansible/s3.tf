/*
resource "oci_objectstorage_bucket" "helpdesk_bucket" {
    namespace      = "axm70tntbzcm" 
    name           = "helpdesk-storage"
    compartment_id = var.compartment_ocid 
    
    storage_tier = "Standard"
    access_type  = "ObjectRead" 
}
*/