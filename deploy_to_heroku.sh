#!/bin/bash

# Heroku Deployment Script for AWS DevTools
# This script automates the deployment of the AWS DevTools application to Heroku

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Heroku CLI is installed
check_heroku_cli() {
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI is not installed."
        echo "Please install it from: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    print_success "Heroku CLI is installed"
}

# Function to check if user is logged into Heroku
check_heroku_login() {
    if ! heroku auth:whoami &> /dev/null; then
        print_error "You are not logged into Heroku."
        echo "Please run: heroku login"
        exit 1
    fi
    print_success "Logged into Heroku as: $(heroku auth:whoami)"
}

# Function to check if git is initialized
check_git() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "Git repository not initialized."
        exit 1
    fi
    print_success "Git repository found"
}

# Main deployment function
deploy() {
    local APP_NAME=$1
    local DEPLOY_WORKER=$2
    
    print_info "Starting deployment to Heroku..."
    
    # Check prerequisites
    check_heroku_cli
    check_heroku_login
    check_git
    
    # Create or use existing Heroku app
    if heroku apps:info --app "$APP_NAME" &> /dev/null; then
        print_warning "App '$APP_NAME' already exists. Using existing app."
    else
        print_info "Creating new Heroku app: $APP_NAME"
        heroku create "$APP_NAME"
        print_success "App created successfully"
    fi
    
    # Set buildpack for Python
    print_info "Setting Python buildpack..."
    heroku buildpacks:set heroku/python --app "$APP_NAME"
    
    # Configure environment variables
    print_info "Configuring environment variables..."
    
    # Check if .env file exists for local reference
    if [ -f .env ]; then
        print_warning "Found .env file. Remember to manually set sensitive variables on Heroku."
        echo "You can set them using: heroku config:set KEY=VALUE --app $APP_NAME"
    else
        print_warning "No .env file found. You'll need to set environment variables manually."
    fi
    
    # Prompt for required AWS credentials if not already set
    print_info "Checking required environment variables on Heroku..."
    
    if ! heroku config:get AWS_ACCESS_KEY_ID --app "$APP_NAME" &> /dev/null; then
        print_warning "AWS_ACCESS_KEY_ID not set on Heroku."
        read -p "Enter AWS_ACCESS_KEY_ID (or press Enter to skip): " aws_key
        if [ ! -z "$aws_key" ]; then
            heroku config:set AWS_ACCESS_KEY_ID="$aws_key" --app "$APP_NAME"
        fi
    fi
    
    if ! heroku config:get AWS_SECRET_ACCESS_KEY --app "$APP_NAME" &> /dev/null; then
        print_warning "AWS_SECRET_ACCESS_KEY not set on Heroku."
        read -sp "Enter AWS_SECRET_ACCESS_KEY (or press Enter to skip): " aws_secret
        echo
        if [ ! -z "$aws_secret" ]; then
            heroku config:set AWS_SECRET_ACCESS_KEY="$aws_secret" --app "$APP_NAME"
        fi
    fi
    
    if ! heroku config:get AWS_DEFAULT_REGION --app "$APP_NAME" &> /dev/null; then
        print_warning "AWS_DEFAULT_REGION not set on Heroku."
        read -p "Enter AWS_DEFAULT_REGION (default: us-east-1): " aws_region
        aws_region=${aws_region:-us-east-1}
        heroku config:set AWS_DEFAULT_REGION="$aws_region" --app "$APP_NAME"
    fi
    
    # Check if Celery worker is needed
    if [ "$DEPLOY_WORKER" = "true" ]; then
        print_info "Celery worker deployment enabled. Checking for MongoDB..."
        
        # Check MongoDB
        if ! heroku config:get MONGODB_URI --app "$APP_NAME" &> /dev/null; then
            print_warning "MONGODB_URI not set (required for Celery)."
            read -p "Enter MONGODB_URI (or press Enter to skip and set later): " mongodb_uri
            if [ ! -z "$mongodb_uri" ]; then
                heroku config:set MONGODB_URI="$mongodb_uri" --app "$APP_NAME"
                print_success "MONGODB_URI configured"
            else
                echo "Remember to set MONGODB_URI before starting the worker:"
                echo "  heroku config:set MONGODB_URI='your_mongodb_connection_string' --app $APP_NAME"
            fi
        else
            print_success "MONGODB_URI already configured"
        fi
    fi
    
    # Commit any uncommitted changes (optional)
    if [[ -n $(git status -s) ]]; then
        print_warning "You have uncommitted changes."
        read -p "Do you want to commit them before deploying? (y/n): " commit_changes
        if [ "$commit_changes" = "y" ]; then
            git add -A
            read -p "Enter commit message: " commit_msg
            git commit -m "$commit_msg"
            print_success "Changes committed"
        fi
    fi
    
    # Add Heroku remote if it doesn't exist
    if ! git remote | grep -q heroku; then
        print_info "Adding Heroku remote..."
        heroku git:remote --app "$APP_NAME"
    fi
    
    # Deploy to Heroku
    print_info "Deploying to Heroku..."
    git push heroku main
    
    print_success "Deployment completed!"
    
    # Scale dynos
    print_info "Scaling web dyno..."
    heroku ps:scale web=1 --app "$APP_NAME"
    
    if [ "$DEPLOY_WORKER" = "true" ]; then
        print_info "Scaling worker dyno..."
        heroku ps:scale worker=1 --app "$APP_NAME"
    fi
    
    # Show app info
    print_info "Application info:"
    heroku apps:info --app "$APP_NAME"
    
    # Open the app
    print_success "Deployment successful!"
    echo ""
    echo "Your app is deployed at: https://$APP_NAME.herokuapp.com"
    echo ""
    echo "Useful commands:"
    echo "  View logs:           heroku logs --tail --app $APP_NAME"
    echo "  Open app:            heroku open --app $APP_NAME"
    echo "  Run migrations:      heroku run <command> --app $APP_NAME"
    echo "  Set config var:      heroku config:set KEY=VALUE --app $APP_NAME"
    echo "  Check dyno status:   heroku ps --app $APP_NAME"
    echo ""
    
    read -p "Do you want to open the app in browser? (y/n): " open_app
    if [ "$open_app" = "y" ]; then
        heroku open --app "$APP_NAME"
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -a, --app NAME       Heroku app name (required)"
    echo "  -w, --worker         Deploy with Celery worker dyno"
    echo "  -h, --help           Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --app my-aws-devtools --worker"
    echo ""
}

# Parse command line arguments
APP_NAME=""
DEPLOY_WORKER="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        -a|--app)
            APP_NAME="$2"
            shift 2
            ;;
        -w|--worker)
            DEPLOY_WORKER="true"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required arguments
if [ -z "$APP_NAME" ]; then
    print_error "App name is required"
    usage
    exit 1
fi

# Run deployment
deploy "$APP_NAME" "$DEPLOY_WORKER"

