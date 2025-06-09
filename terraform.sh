#!/bin/bash

set -e

cd "$(dirname "$0")"

# Set the source environment file
ENV_FILE=".env/datadog.env"

# Function to run terraform command in docker
run_terraform() {
    docker compose \
        -f ./terraform/compose.yml \
        run -it --rm -e "TERM=xterm-256color" \
        terraform "$@"
}

# Function to run terraform output in docker (non-interactive)
run_terraform_output() {
    docker compose \
        -f ./terraform/compose.yml \
        run --rm \
        terraform output "$@"
}

# Function to generate terraform.tfvars from .env files
generate_tfvars() {
    echo "Generating terraform.tfvars from environment variables..."
    
    # Clear or create terraform.tfvars
    > terraform/conf/terraform.tfvars

    # Read from env file and write to terraform.tfvars
    if [ -f "$ENV_FILE" ]; then
        # Extract and format variables
        if grep -q "^DD_API_KEY=" "$ENV_FILE"; then
            echo "dd_api_key = \"$(grep "^DD_API_KEY=" "$ENV_FILE" | cut -d '=' -f2-)\"" >> terraform/conf/terraform.tfvars
        fi
        if grep -q "^DD_APP_KEY=" "$ENV_FILE"; then
            echo "dd_app_key = \"$(grep "^DD_APP_KEY=" "$ENV_FILE" | cut -d '=' -f2-)\"" >> terraform/conf/terraform.tfvars
        fi
        if grep -q "^DD_SITE=" "$ENV_FILE"; then
            echo "dd_site = \"$(grep "^DD_SITE=" "$ENV_FILE" | cut -d '=' -f2-)\"" >> terraform/conf/terraform.tfvars
        fi
        if grep -q "^DD_ENV=" "$ENV_FILE"; then
            echo "dd_env = \"$(grep "^DD_ENV=" "$ENV_FILE" | cut -d '=' -f2-)\"" >> terraform/conf/terraform.tfvars
        fi
        if grep -q "^DD_TAGS=" "$ENV_FILE"; then
            echo "dd_tags = \"$(grep "^DD_TAGS=" "$ENV_FILE" | cut -d '=' -f2-),owner:terraform\"" >> terraform/conf/terraform.tfvars
        fi
        if grep -q "^NOTIF_EMAIL=" "$ENV_FILE"; then
            echo "notif_email = \"$(grep "^NOTIF_EMAIL=" "$ENV_FILE" | cut -d '=' -f2-)\"" >> terraform/conf/terraform.tfvars
        fi
    else
        echo "Warning: $ENV_FILE not found"
    fi
        
    echo "Generated terraform/conf/terraform.tfvars"
}

# Function to generate environment files from terraform outputs
generate_env_files() {
    echo "Generating environment files from Terraform outputs..."
    
    # Get all outputs in JSON format
    OUTPUTS=$(run_terraform_output -json)
    
    # Generate synthetics.env
    {
        echo "DATADOG_ACCESS_KEY='$(echo "$OUTPUTS" | jq -r '.private_location_access_key.value')'"
        echo "DATADOG_SECRET_ACCESS_KEY='$(echo "$OUTPUTS" | jq -r '.private_location_secret_access_key.value')'"
        echo "DATADOG_PUBLIC_KEY_PEM='$(echo "$OUTPUTS" | jq -r '.private_location_public_key_pem.value')'"
        echo "DATADOG_PRIVATE_KEY='$(echo "$OUTPUTS" | jq -r '.private_location_private_key.value')'"
    } > .env/synthetics.env
    
    # Generate rum.env
    {
        echo "DD_APPLICATION_ID='$(echo "$OUTPUTS" | jq -r '.rum_application_id.value')'"
        echo "DD_CLIENT_TOKEN='$(echo "$OUTPUTS" | jq -r '.rum_client_token.value')'"
    } > .env/rum.env
}

# Main script logic
case "$1" in
    "init")
        generate_tfvars
        run_terraform init
        ;;
    "plan")
        generate_tfvars
        run_terraform plan
        ;;
    "apply")
        generate_tfvars
        run_terraform apply -auto-approve
        generate_env_files
        ;;
    "destroy")
        generate_tfvars
        run_terraform destroy -auto-approve
        ;;
    "output")
        run_terraform output
        generate_env_files
        ;;
    "--help"|"-h"|"help")
        run_terraform --help
        ;;
    "--version"|"-v"|"version")
        run_terraform version
        ;;
    *)
        echo "Usage: $0 {init|plan|apply|destroy|output|help|version}"
        exit 1
        ;;
esac
