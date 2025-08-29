from __future__ import annotations
import os
import shutil
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

class IDEIntegration:
    """Handles detection and opening of supported IDEs with generated code."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.supported_ides = {
            "vscode": {
                "name": "Visual Studio Code",
                "executables": {
                    "windows": ["code.cmd", "code.exe", "code"],
                    "darwin": ["code"],
                    "linux": ["code"]
                },
                "fallback_paths": {
                    "windows": [
                        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
                        os.path.expandvars(r"%PROGRAMFILES%\Microsoft VS Code\bin\code.cmd"),
                        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft VS Code\bin\code.cmd"),
                        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                        os.path.expandvars(r"%PROGRAMFILES%\Microsoft VS Code\Code.exe"),
                        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft VS Code\Code.exe")
                    ],
                    "darwin": [
                        "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code",
                        "/usr/local/bin/code"
                    ],
                    "linux": [
                        "/usr/bin/code",
                        "/usr/local/bin/code",
                        "/snap/bin/code"
                    ]
                },
                "supports": ["web", "react", "flutter"],
                "workspace_files": {
                    "web": ".vscode/settings.json",
                    "react": ".vscode/settings.json", 
                    "flutter": ".vscode/launch.json"
                }
            },
            "webstorm": {
                "name": "WebStorm",
                "executables": {
                    "windows": ["webstorm64.exe", "webstorm"],
                    "darwin": ["webstorm"],
                    "linux": ["webstorm"]
                },
                "fallback_paths": {
                    "windows": [
                        os.path.expandvars(r"%LOCALAPPDATA%\JetBrains\Toolbox\apps\WebStorm\ch-0\*\bin\webstorm64.exe"),
                        os.path.expandvars(r"%PROGRAMFILES%\JetBrains\WebStorm *\bin\webstorm64.exe")
                    ],
                    "darwin": ["/Applications/WebStorm.app/Contents/MacOS/webstorm"],
                    "linux": ["/opt/webstorm/bin/webstorm.sh"]
                },
                "supports": ["web", "react"],
                "workspace_files": {
                    "web": ".idea/workspace.xml",
                    "react": ".idea/workspace.xml"
                }
            },
            "android_studio": {
                "name": "Android Studio",
                "executables": {
                    "windows": ["studio64.exe", "studio"],
                    "darwin": ["studio"],
                    "linux": ["studio"]
                },
                "supports": ["flutter"],
                "workspace_files": {
                    "flutter": ".idea/workspace.xml"
                }
            },
            "intellij": {
                "name": "IntelliJ IDEA",
                "executables": {
                    "windows": ["idea64.exe", "idea"],
                    "darwin": ["idea"],
                    "linux": ["idea"]
                },
                "supports": ["web", "react", "flutter"],
                "workspace_files": {
                    "web": ".idea/workspace.xml",
                    "react": ".idea/workspace.xml",
                    "flutter": ".idea/workspace.xml"
                }
            },
            "sublime": {
                "name": "Sublime Text",
                "executables": {
                    "windows": ["subl.exe", "sublime_text.exe"],
                    "darwin": ["subl"],
                    "linux": ["subl", "sublime_text"]
                },
                "supports": ["web", "react", "flutter"],
                "workspace_files": {}
            },
            "atom": {
                "name": "Atom",
                "executables": {
                    "windows": ["atom.exe"],
                    "darwin": ["atom"],
                    "linux": ["atom"]
                },
                "supports": ["web", "react", "flutter"],
                "workspace_files": {}
            }
        }

    def _find_executable(self, ide_key: str) -> Optional[str]:
        """Find the executable path for a given IDE."""
        ide_info = self.supported_ides.get(ide_key, {})
        
        # First try PATH-based detection
        executables = ide_info.get("executables", {}).get(self.system, [])
        for exe in executables:
            if shutil.which(exe):
                return exe
        
        # Then try fallback paths
        fallback_paths = ide_info.get("fallback_paths", {}).get(self.system, [])
        for path in fallback_paths:
            # Handle wildcards in paths
            if "*" in path:
                import glob
                matches = glob.glob(path)
                for match in matches:
                    if os.path.isfile(match) and os.access(match, os.X_OK):
                        return match
            else:
                if os.path.isfile(path) and os.access(path, os.X_OK):
                    return path
        
        return None

    def detect_available_ides(self) -> List[Dict[str, str]]:
        """Detect which IDEs are installed and available."""
        available = []
        
        for ide_key, ide_info in self.supported_ides.items():
            executable = self._find_executable(ide_key)
            if executable:
                available.append({
                    "key": ide_key,
                    "name": ide_info["name"],
                    "executable": executable,
                    "supports": ide_info["supports"]
                })
                    
        return available

    def get_compatible_ides(self, framework: str) -> List[Dict[str, str]]:
        """Get IDEs that support the given framework."""
        available = self.detect_available_ides()
        return [ide for ide in available if framework in ide["supports"]]

    def create_workspace_files(self, project_dir: Path, framework: str, ide_key: str) -> None:
        """Create IDE-specific workspace/configuration files."""
        ide_info = self.supported_ides.get(ide_key, {})
        workspace_file = ide_info.get("workspace_files", {}).get(framework)
        
        if not workspace_file:
            return
            
        workspace_path = project_dir / workspace_file
        workspace_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create IDE-specific configuration
        if ide_key == "vscode":
            self._create_vscode_config(workspace_path, framework)
        elif ide_key in ["webstorm", "intellij", "android_studio"]:
            self._create_jetbrains_config(workspace_path, framework)

    def _create_vscode_config(self, config_path: Path, framework: str) -> None:
        """Create VS Code workspace configuration."""
        config = {
            "folders": [{"path": "."}],
            "settings": {
                "editor.tabSize": 2,
                "editor.insertSpaces": True,
                "files.eol": "\n"
            },
            "extensions": {
                "recommendations": []
            }
        }
        
        if framework == "react":
            config["settings"].update({
                "emmet.includeLanguages": {"javascript": "javascriptreact"},
                "typescript.preferences.quoteStyle": "single"
            })
            config["extensions"]["recommendations"].extend([
                "ms-vscode.vscode-typescript-next",
                "bradlc.vscode-tailwindcss",
                "esbenp.prettier-vscode"
            ])
        elif framework == "flutter":
            config["extensions"]["recommendations"].extend([
                "dart-code.dart-code",
                "dart-code.flutter"
            ])
        elif framework == "web":
            config["extensions"]["recommendations"].extend([
                "ms-vscode.live-server",
                "bradlc.vscode-tailwindcss"
            ])
            
        if config_path.name == "settings.json":
            # Just settings for .vscode/settings.json
            config_path.write_text(json.dumps(config["settings"], indent=2), encoding="utf-8")
        else:
            # Full workspace file
            config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    def _create_jetbrains_config(self, config_path: Path, framework: str) -> None:
        """Create JetBrains IDE workspace configuration."""
        # Basic workspace.xml for JetBrains IDEs
        workspace_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<project version="4">
  <component name="ChangeListManager">
    <list default="true" id="default" name="Default Changelist" comment="" />
    <option name="SHOW_DIALOG" value="false" />
    <option name="HIGHLIGHT_CONFLICTS" value="true" />
    <option name="HIGHLIGHT_NON_ACTIVE_CHANGELIST" value="false" />
    <option name="LAST_RESOLUTION" value="IGNORE" />
  </component>
  <component name="ProjectViewState">
    <option name="hideEmptyMiddlePackages" value="true" />
    <option name="showLibraryContents" value="true" />
  </component>
</project>'''
        config_path.write_text(workspace_xml, encoding="utf-8")

    def open_in_ide(self, project_dir: Path, ide_key: str, framework: str) -> Tuple[bool, str]:
        """Open the project directory in the specified IDE."""
        try:
            # Create workspace files first
            self.create_workspace_files(project_dir, framework, ide_key)
            
            # Get IDE executable using the improved detection
            executable = self._find_executable(ide_key)
            if not executable:
                ide_info = self.supported_ides.get(ide_key, {})
                return False, f"IDE '{ide_info.get('name', ide_key)}' not found. Please ensure it's installed and accessible."
                
            # Launch IDE with project directory
            if self.system == "windows":
                # Use subprocess.Popen for Windows to avoid blocking
                subprocess.Popen([executable, str(project_dir)], 
                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                               shell=True)
            else:
                # Use subprocess.Popen for Unix-like systems
                subprocess.Popen([executable, str(project_dir)], 
                               start_new_session=True)
                
            ide_info = self.supported_ides.get(ide_key, {})
            return True, f"Opened project in {ide_info.get('name', ide_key)}"
            
        except Exception as e:
            return False, f"Failed to open IDE: {str(e)}"

    def get_framework_specific_instructions(self, framework: str, ide_key: str) -> str:
        """Get framework and IDE specific setup instructions."""
        instructions = {
            "web": {
                "vscode": "Open index.html with Live Server extension, or use 'python -m http.server 8000'",
                "webstorm": "Right-click index.html and select 'Open in Browser'",
                "default": "Open index.html in your browser or serve with a local server"
            },
            "react": {
                "vscode": "Run 'npm install' then 'npm start' in the terminal",
                "webstorm": "WebStorm will auto-detect React project. Run 'npm install' then 'npm start'",
                "default": "Run 'npm install' then 'npm start' to start development server"
            },
            "flutter": {
                "vscode": "Ensure Flutter and Dart extensions are installed. Run 'flutter run'",
                "android_studio": "Android Studio will auto-detect Flutter project. Click 'Run' button",
                "default": "Run 'flutter pub get' then 'flutter run' to start the app"
            }
        }
        
        return instructions.get(framework, {}).get(ide_key, 
                instructions.get(framework, {}).get("default", "No specific instructions available"))
