#!/usr/bin/env bash
LIB_V=${LIB_VERSION:-v0}
echo "publishing lib..."
charmcraft publish-lib "charms.deferral-queue-editor.$LIB_V.editor.py"  # $ TEMPLATE: Filled in by ./scripts/init.sh
