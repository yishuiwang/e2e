#!/bin/bash
# 激活LangGraph Agent虚拟环境
echo "🔄 激活LangGraph Agent虚拟环境..."
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate langgraph_agent
echo "✅ 虚拟环境已激活: langgraph_agent"
echo "🐍 Python路径: $(which python)"
echo "📦 Python版本: $(python --version)" 