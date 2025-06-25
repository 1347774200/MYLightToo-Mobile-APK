#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端应用构建脚本
自动化构建Android APK的完整流程
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class MobileAppBuilder:
    """移动端应用构建器"""
    
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.build_dir = self.project_dir / "mobile_build"
        self.requirements_installed = False
        
        print("🏗️ 移动端应用构建器初始化")
    
    def check_environment(self):
        """检查构建环境"""
        print("\n1️⃣ 检查构建环境...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version.major != 3 or python_version.minor < 8:
            print("❌ 需要Python 3.8或更高版本")
            return False
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
        
        # 检查必要的工具
        tools = ['git', 'java']
        for tool in tools:
            if shutil.which(tool) is None:
                print(f"❌ 缺少工具: {tool}")
                return False
            print(f"✅ 工具可用: {tool}")
        
        return True
    
    def install_dependencies(self):
        """安装构建依赖"""
        print("\n2️⃣ 安装构建依赖...")
        
        try:
            # 安装buildozer
            print("📦 安装buildozer...")
            subprocess.run([sys.executable, "-m", "pip", "install", "buildozer"], check=True)
            print("✅ buildozer安装成功")
            
            # 安装Kivy依赖
            print("📦 安装Kivy依赖...")
            kivy_deps = [
                "kivy[base]==2.1.0",
                "kivymd",
                "requests",
                "websocket-client",
                "certifi"
            ]
            
            for dep in kivy_deps:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
                print(f"✅ {dep} 安装成功")
            
            self.requirements_installed = True
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ 依赖安装失败: {e}")
            return False
    
    def prepare_build_directory(self):
        """准备构建目录"""
        print("\n3️⃣ 准备构建目录...")
        
        try:
            # 创建构建目录
            if self.build_dir.exists():
                shutil.rmtree(self.build_dir)
            self.build_dir.mkdir(parents=True)
            print(f"✅ 构建目录创建: {self.build_dir}")
            
            # 复制必要文件
            files_to_copy = [
                "main.py",
                "mobile_controller_app.py",
                "buildozer.spec"
            ]
            
            for file_name in files_to_copy:
                src = self.project_dir / file_name
                dst = self.build_dir / file_name
                
                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"✅ 复制文件: {file_name}")
                else:
                    print(f"⚠️ 文件不存在: {file_name}")
            
            return True
            
        except Exception as e:
            print(f"❌ 准备构建目录失败: {e}")
            return False
    
    def build_apk(self):
        """构建APK"""
        print("\n4️⃣ 构建APK...")
        
        try:
            # 切换到构建目录
            original_dir = os.getcwd()
            os.chdir(self.build_dir)
            
            print("🔨 开始构建APK（这可能需要较长时间）...")
            
            # 运行buildozer构建
            result = subprocess.run(
                ["buildozer", "android", "debug"],
                capture_output=True,
                text=True,
                timeout=3600  # 1小时超时
            )
            
            # 恢复原目录
            os.chdir(original_dir)
            
            if result.returncode == 0:
                print("✅ APK构建成功！")
                
                # 查找生成的APK文件
                apk_files = list(self.build_dir.glob("bin/*.apk"))
                if apk_files:
                    apk_file = apk_files[0]
                    print(f"📱 APK文件位置: {apk_file}")
                    
                    # 复制APK到项目根目录
                    final_apk = self.project_dir / f"multimedia_show_controller.apk"
                    shutil.copy2(apk_file, final_apk)
                    print(f"📱 APK已复制到: {final_apk}")
                    
                return True
            else:
                print("❌ APK构建失败")
                print("构建输出:")
                print(result.stdout)
                print("错误信息:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ 构建超时（超过1小时）")
            return False
        except Exception as e:
            print(f"❌ 构建过程出错: {e}")
            return False
    
    def create_installation_guide(self):
        """创建安装指南"""
        print("\n5️⃣ 创建安装指南...")
        
        guide_content = """
# 文旅多媒体演出控制 - 移动端安装指南

## 📱 APK安装步骤

### 1. 准备平板设备
- Android 5.0 (API 21) 或更高版本
- 至少1GB可用存储空间
- 网络连接（WiFi推荐）

### 2. 启用未知来源安装
1. 打开平板的"设置"
2. 进入"安全"或"隐私"设置
3. 启用"未知来源"或"允许安装未知应用"

### 3. 安装APK
1. 将APK文件传输到平板（USB、网络传输等）
2. 在平板上找到APK文件
3. 点击APK文件开始安装
4. 按照提示完成安装

### 4. 配置网络连接
1. 确保平板与主控制系统在同一网络
2. 启动应用
3. 在登录界面输入主控制系统的IP地址
4. 使用有效的用户名和密码登录

## 🔧 网络配置

### 主控制系统设置
- 确保防火墙允许端口8080的访问
- 启动移动端API服务器
- 记录主控制系统的IP地址

### 平板网络设置
- 连接到与主控制系统相同的WiFi网络
- 确保网络稳定，延迟较低

## 👥 用户账户

### 默认账户
- 管理员: admin / admin123
- 操作员: operator / op123  
- 访客: guest / guest

### 权限说明
- **管理员**: 所有功能权限
- **操作员**: 场景控制、灯光控制、音频控制
- **访客**: 仅查看权限

## 🎭 使用说明

### 场景控制
1. 在场景列表中选择要播放的场景
2. 点击"播放"按钮开始演出
3. 使用"暂停"和"停止"按钮控制播放

### 快速控制
- **音量调节**: 拖动音量滑块
- **灯光控制**: 点击相应的灯光按钮
- **紧急停止**: 点击红色紧急停止按钮

### 状态监控
- 顶部状态栏显示连接状态和当前时间
- 右侧面板显示系统状态信息

## ⚠️ 注意事项

1. **网络稳定性**: 确保WiFi连接稳定，避免演出中断
2. **电量管理**: 演出前确保平板电量充足
3. **权限管理**: 根据操作人员职责分配合适的账户权限
4. **备用方案**: 准备备用控制方式，以防移动端故障

## 🔧 故障排除

### 连接问题
- 检查网络连接
- 确认IP地址正确
- 检查防火墙设置

### 登录问题
- 确认用户名和密码
- 检查用户权限设置

### 控制问题
- 确认主控制系统正常运行
- 检查API服务器状态

## 📞 技术支持

如遇到技术问题，请联系技术支持团队。
"""
        
        try:
            guide_file = self.project_dir / "移动端安装指南.md"
            with open(guide_file, 'w', encoding='utf-8') as f:
                f.write(guide_content)
            
            print(f"✅ 安装指南已创建: {guide_file}")
            return True
            
        except Exception as e:
            print(f"❌ 创建安装指南失败: {e}")
            return False
    
    def build_complete(self):
        """构建完成"""
        print("\n" + "="*50)
        print("🎉 移动端应用构建完成！")
        print("\n📦 构建产物:")
        
        apk_file = self.project_dir / "multimedia_show_controller.apk"
        if apk_file.exists():
            print(f"   📱 APK文件: {apk_file}")
            print(f"   📏 文件大小: {apk_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        guide_file = self.project_dir / "移动端安装指南.md"
        if guide_file.exists():
            print(f"   📖 安装指南: {guide_file}")
        
        print("\n🚀 下一步:")
        print("   1. 将APK文件传输到Android平板")
        print("   2. 按照安装指南进行安装和配置")
        print("   3. 在主控制系统中启动API服务器")
        print("   4. 测试移动端控制功能")
    
    def run_build(self):
        """运行完整构建流程"""
        print("🚀 开始移动端应用构建流程")
        
        # 检查环境
        if not self.check_environment():
            print("❌ 环境检查失败，构建终止")
            return False
        
        # 安装依赖
        if not self.install_dependencies():
            print("❌ 依赖安装失败，构建终止")
            return False
        
        # 准备构建目录
        if not self.prepare_build_directory():
            print("❌ 构建目录准备失败，构建终止")
            return False
        
        # 构建APK
        if not self.build_apk():
            print("❌ APK构建失败，构建终止")
            return False
        
        # 创建安装指南
        self.create_installation_guide()
        
        # 构建完成
        self.build_complete()
        
        return True


def main():
    """主函数"""
    print("📱 文旅多媒体演出控制 - 移动端构建工具")
    print("=" * 60)
    
    builder = MobileAppBuilder()
    
    try:
        success = builder.run_build()
        if success:
            print("\n✅ 构建流程完成！")
            return 0
        else:
            print("\n❌ 构建流程失败！")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断构建")
        return 1
    except Exception as e:
        print(f"\n💥 构建过程出现异常: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
