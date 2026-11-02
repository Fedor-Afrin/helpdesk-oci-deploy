/*
resource "oci_objectstorage_bucket" "helpdesk_bucket" {
    namespace      = "YOUR_OBJECT_STORAGE_NAMESPACE"
    name           = "helpdesk-storage"
    compartment_id = var.compartment_ocid

    storage_tier = "Standard"
    access_type  = "ObjectRead"
}
*/
