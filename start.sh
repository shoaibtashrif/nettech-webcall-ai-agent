#!/bin/bash

echo "🚀 Starting NetTech WebCall AI Agent with Pinggy Tunnel"
echo "======================================================"

# Function to get Pinggy URL with better timeout handling
get_pinggy_url() {
    echo "🔗 Establishing Pinggy tunnel..."
    
    # Create a named pipe for communication
    local pipe=$(mktemp -u)
    mkfifo "$pipe"
    
    # Start SSH in background with shorter timeout
    (ssh -p 443 -o StrictHostKeyChecking=no -o ConnectTimeout=10 -R0:localhost:5004 a.pinggy.io > "$pipe" 2>&1) &
    local ssh_pid=$!
    
    # Read from pipe with timeout
    local pinggy_output
    if pinggy_output=$(timeout 12 cat "$pipe"); then
        # Extract HTTPS URL
        local https_url=$(echo "$pinggy_output" | grep -o "https://[a-zA-Z0-9.-]*\.pinggy\.link" | head -1)
        
        # Kill the SSH process
        kill $ssh_pid 2>/dev/null
        rm -f "$pipe"
        
        if [ -n "$https_url" ]; then
            echo "$https_url"
            return 0
        fi
    fi
    
    # Cleanup
    kill $ssh_pid 2>/dev/null
    rm -f "$pipe"
    echo "❌ Failed to get Pinggy URL"
    return 1
}

# Function to update .env file
update_env_file() {
    local new_url=$1
    local env_file=".env"
    
    if [ ! -f "$env_file" ]; then
        echo "❌ .env file not found!"
        return 1
    fi
    
    if grep -q "TOOLS_BASE_URL=" "$env_file"; then
        sed -i.bak "s|TOOLS_BASE_URL=.*|TOOLS_BASE_URL=$new_url|" "$env_file"
        echo "✅ Updated TOOLS_BASE_URL: $new_url"
    else
        echo "TOOLS_BASE_URL=$new_url" >> "$env_file"
        echo "✅ Added TOOLS_BASE_URL: $new_url"
    fi
}

# Function to start Python app
start_python_app() {
    echo "🐍 Starting Python application..."
    
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    fi
    
    echo "🎯 Running: python3 run.py"
    python3 run.py
}

# Main function
main() {
    # Get Pinggy URL
    echo "⏳ Setting up tunnel (this may take 10-15 seconds)..."
    PINGGY_URL=$(get_pinggy_url)
    
    if [ $? -ne 0 ] || [ -z "$PINGGY_URL" ]; then
        echo "❌ Tunnel setup failed. Retrying once..."
        sleep 2
        PINGGY_URL=$(get_pinggy_url)
        
        if [ $? -ne 0 ] || [ -z "$PINGGY_URL" ]; then
            echo "❌❌ All tunnel attempts failed. Please check:"
            echo "   - Internet connection"
            echo "   - Pinggy service status" 
            echo "   - Port 443 outbound access"
            exit 1
        fi
    fi
    
    echo "🌐 Pinggy URL: $PINGGY_URL"
    
    # Update .env
    update_env_file "$PINGGY_URL"
    
    # Start app
    start_python_app
}

# Run main
main