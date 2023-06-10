from google.cloud import storage
import os

def download_from_gcs(bucket_name, blob_name, destination_path):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(blob_name)
    
    # Extract the filename from the blob name
    filename = os.path.basename(blob_name)
    
    # Combine the destination directory with the filename to create the complete file path
    destination_file_path = os.path.join(destination_path, filename)
    
    blob.download_to_filename(destination_file_path)
    print(f"File downloaded from GCS bucket: {blob_name} -> {destination_file_path}")

# Example usage
bucket_name = "schooapp2022.appspot.com"
blob_name = "B00L49SKIU - KitchenReady Pulled Pork Shredder Claws _ BBQ Meat 2023-06-07.csv"
destination_path = "/Users/datax/aivahub"

download_from_gcs(bucket_name, blob_name, destination_path)
