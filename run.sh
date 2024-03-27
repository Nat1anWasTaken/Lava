#!/bin/bash

# Function to display ASCII art
display_ascii_art() {
    cat << "EOF"
==============================
.____
|    |   _____ ___  _______
|    |   \__  \\  \/ /\__  \
|    |___ / __ \\   /  / __ \_
|_______ (____  /\_/  (____  /
        \/    \/           \/
==============================
EOF
}

# Function to check if Docker is installed and available
check_docker() {
    if command -v docker &> /dev/null; then
        echo "Docker is available."
        return 0
    else
        echo "Docker is not available."
        return 1
    fi
}

# Function to check if Podman is installed and available
check_podman() {
    if command -v podman &> /dev/null; then
        echo "Podman is available."
        return 0
    else
        echo "Podman is not available."
        return 1
    fi
}

# Function to install Podman
install_podman() {
    local package_manager
    if command -v apt &> /dev/null; then
        package_manager="apt"
    elif command -v yum &> /dev/null; then
        package_manager="yum"
    elif command -v dnf &> /dev/null; then
        package_manager="dnf"
    elif command -v pacman &> /dev/null; then
        package_manager="pacman"
    elif command -v zypper &> /dev/null; then
        package_manager="zypper"
    else
        echo "Unsupported package manager. Please install Podman manually."
        exit 1
    fi

    echo "Installing Podman using $package_manager..."
    case $package_manager in
        "apt")
            sudo apt update && sudo apt install -y podman
            ;;
        "yum")
            sudo yum makecache && sudo yum install -y podman
            ;;
        "dnf")
            sudo dnf makecache && sudo dnf install -y podman
            ;;
        "pacman")
            sudo pacman -Syu podman
            ;;
        "zypper")
            sudo zypper --non-interactive refresh && sudo zypper install -y podman
            ;;
        *)
            echo "Unsupported package manager. Please install Podman manually."
            exit 1
            ;;
    esac
}

# Function to check if curl is installed and available
check_curl() {
    if command -v curl &> /dev/null; then
        echo "curl is available."
        return 0
    else
        echo "curl is not available. Installing curl..."
        install_curl
        return $?
    fi
}

# Function to install curl
install_curl() {
    local package_manager
    if command -v apt &> /dev/null; then
        package_manager="apt"
    elif command -v yum &> /dev/null; then
        package_manager="yum"
    elif command -v dnf &> /dev/null; then
        package_manager="dnf"
    elif command -v pacman &> /dev/null; then
        package_manager="pacman"
    elif command -v zypper &> /dev/null; then
        package_manager="zypper"
    else
        echo "Unsupported package manager. Please install curl manually."
        exit 1
    fi

    echo "Installing curl using $package_manager..."
    case $package_manager in
        "apt")
            sudo apt update && sudo apt install -y curl
            ;;
        "yum")
            sudo yum makecache && sudo yum install -y curl
            ;;
        "dnf")
            sudo dnf makecache && sudo dnf install -y curl
            ;;
        "pacman")
            sudo pacman -Syu curl
            ;;
        "zypper")
            sudo zypper --non-interactive refresh && sudo zypper install -y curl
            ;;
        *)
            echo "Unsupported package manager. Please install curl manually."
            exit 1
            ;;
    esac
}

# Check if Docker is available
if check_docker; then
    CONTAINER_RUNTIME="docker"
elif check_podman; then
    CONTAINER_RUNTIME="podman"
else
    install_podman
    CONTAINER_RUNTIME="podman"
fi

echo "Using $CONTAINER_RUNTIME as container runtime."

# Check if curl is available
if ! check_curl; then
    echo "Failed to install curl. Exiting."
    exit 1
fi

# Function to prompt user for input
get_input() {
    local var_name="$1"
    read -p "Enter your $var_name: " value
    echo "$var_name=$value"
}

# Display ASCII art
display_ascii_art

# Download configuration files if they don't exist
echo "Checking if configuration files exist..."
mkdir -p ./configs
if [ ! -f "./configs/application.yml" ]; then
    echo "Downloading application.yml..."
    curl -o ./configs/application.yml -L https://raw.githubusercontent.com/Nat1anWasTaken/Lava/master/configs/application.yml
fi
if [ ! -f "./configs/icons.json" ]; then
    echo "Downloading icons.json..."
    curl -o ./configs/icons.json -L https://raw.githubusercontent.com/Nat1anWasTaken/Lava/master/configs/icons.json
fi
if [ ! -f "./configs/lavalink.json" ]; then
    echo "Downloading lavalink.json..."
    curl -o ./configs/lavalink.json -L https://raw.githubusercontent.com/Nat1anWasTaken/Lava/master/configs/lavalink.json
fi

# Check if stack.env exists
if [ ! -f "stack.env" ]; then
    # Prompt user for values
    TOKEN=$(get_input "TOKEN")
    SPOTIFY_CLIENT_ID=$(get_input "SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET=$(get_input "SPOTIFY_CLIENT_SECRET")

    # Save values to stack.env
    echo -e "$TOKEN\n$SPOTIFY_CLIENT_ID\n$SPOTIFY_CLIENT_SECRET\nLAVALINK_SERVER=1" > stack.env
    echo "Values saved to stack.env"
fi

# Run the container with the specified command using the chosen runtime
$CONTAINER_RUNTIME run --restart always --env-file stack.env -v ./configs:/lava/configs ghcr.io/nat1anwastaken/lava:latest
