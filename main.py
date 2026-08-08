def main():
    print("Hello from cmd-tool!")

    from services.plugin_loader_service import discover_plugins

    plugins = discover_plugins()
    for plugin in plugins:
        print(f"发现插件: {plugin}")
        

if __name__ == "__main__":
    main()
