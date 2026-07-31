#!/bin/bash
# Script to synchronize Zenoh configuration files between ws_rmw_zenoh and meshcontrolplane

WS_ZENOH_DIR="/home/nvidia/ws_rmw_zenoh/src/rmw_zenoh-humble/rmw_zenoh_cpp/config/tcp"
REPO_ZENOH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../config/zenoh" && pwd)"

case "$1" in
    import)
        echo "Importing configuration from ws_rmw_zenoh -> meshcontrolplane..."
        cp "$WS_ZENOH_DIR/zenoh_router_tcp.json5" "$REPO_ZENOH_DIR/"
        cp "$WS_ZENOH_DIR/zenoh_peer_tcp.json5" "$REPO_ZENOH_DIR/"
        echo "Done. Run 'git status' or 'git diff' to view changes."
        ;;
    export)
        echo "Exporting configuration from meshcontrolplane -> ws_rmw_zenoh..."
        cp "$REPO_ZENOH_DIR/zenoh_router_tcp.json5" "$WS_ZENOH_DIR/"
        cp "$REPO_ZENOH_DIR/zenoh_peer_tcp.json5" "$WS_ZENOH_DIR/"
        echo "Done. Applied configuration to ws_rmw_zenoh."
        ;;
    symlink)
        echo "Creating symbolic links from ws_rmw_zenoh to meshcontrolplane..."
        ln -sf "$REPO_ZENOH_DIR/zenoh_router_tcp.json5" "$WS_ZENOH_DIR/zenoh_router_tcp.json5"
        ln -sf "$REPO_ZENOH_DIR/zenoh_peer_tcp.json5" "$WS_ZENOH_DIR/zenoh_peer_tcp.json5"
        echo "Done. Symbolic links established."
        ;;
    *)
        echo "Usage: $0 {import|export|symlink}"
        echo "  import  : Copy updated configs from workspace into git repo"
        echo "  export  : Deploy repo configs to workspace"
        echo "  symlink : Link workspace directly to git repo files (automatic real-time tracking)"
        exit 1
        ;;
esac
