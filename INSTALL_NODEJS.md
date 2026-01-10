# Installing Node.js on Windows

## Quick Installation (Recommended)

### Option 1: Official Installer (Easiest)
1. Download the Windows installer from: https://nodejs.org/
2. Choose the **LTS (Long Term Support)** version (recommended)
3. Run the installer (.msi file)
4. Follow the installation wizard:
   - Accept the license agreement
   - Choose installation directory (default is fine)
   - **Important:** Make sure "Add to PATH" option is checked (it should be by default)
   - Complete the installation
5. **Restart your PowerShell/terminal** after installation

### Option 2: Using Winget (Windows Package Manager)
If you have Windows 10/11 with winget:
```powershell
winget install OpenJS.NodeJS.LTS
```

Then restart your PowerShell terminal.

### Option 3: Using Chocolatey (If installed)
```powershell
choco install nodejs-lts
```

Then restart your PowerShell terminal.

## Verify Installation

After installing and restarting your terminal, verify Node.js is installed:

```powershell
node --version
npm --version
```

You should see version numbers for both commands.

## If Installation Fails

1. Check if you have administrator rights
2. Try running the installer as Administrator
3. Check Windows Defender or antivirus isn't blocking the installation
4. Restart your computer after installation

## After Installation

Once Node.js is installed, you can continue with the frontend setup:

```powershell
cd frontend
npm install
```


