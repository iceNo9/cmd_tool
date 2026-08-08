# cmd_tool

<!-- 项目总体结构 -->
cmd_tool/
│
├── main.py
│
├── ui/
│   ├── pages/          # 页面（MainPage、SettingsPage 等）
│   ├── components/     # 可复用组件（Sidebar、FormPanel、OutputPanel 等）
│   ├── dialogs/        # 各种对话框
│   └── theme.py        # 主题配置
│
├── services/           # 业务逻辑
├── models/             # 数据模型
├── utils/              # 工具函数
│
├── assets/             # 图片、图标、字体等静态资源
└── data/               # 配置、日志、缓存、数据库等运行时数据

cmd_tool/
│
├── main.py
│
├── ui/                         # 第 5 阶段
│   ├── pages/
│   │   ├── main_page.py
│   │   └── settings_page.py
│   │
│   ├── components/
│   │   ├── sidebar.py
│   │   ├── tool_list.py
│   │   ├── form_panel.py
│   │   └── output_panel.py
│   │
│   ├── dialogs/
│   │   └── ...
│   │
│   └── theme.py
│
├── services/                   # 第 3 阶段
│   ├── task_service.py
│   ├── config_service.py
│   └── history_service.py
│
├── models/                     # 第 2 阶段
│   ├── config.py
│   ├── task.py
│   └── state.py
│
├── utils/                      # 第 1~3 阶段逐渐整理
│   ├── logger.py
│   └── file_utils.py
│
├── assets/
└── data/

<!-- 构建顺序 -->
① 分析现有代码
        ↓
② Models
        ↓
③ Services
        ↓
④ Utils
        ↓
⑤ Flet UI 基础框架
        ↓
⑥ Components
        ↓
⑦ Pages
        ↓
⑧ 状态管理
        ↓
⑨ UI ↔ Service 接通
        ↓
⑩ 重构 / 测试 / 清理