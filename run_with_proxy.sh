#!/bin/bash
set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Proxy configuration
export http_proxy="http://127.0.0.1:20171"
export https_proxy="http://127.0.0.1:20171"
export all_proxy="socks5://127.0.0.1:20171"

echo "🚀 Starting MCP services with proxy configuration:"
echo "   HTTP_PROXY: $http_proxy"
echo "   HTTPS_PROXY: $https_proxy"
echo "   ALL_PROXY: $all_proxy"
echo ""

# Call the original run script with all arguments
"$SCRIPT_DIR/run.sh" "$@"
