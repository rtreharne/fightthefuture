# Installing VS Code and R on an MWS machine

This guide explains how to install Visual Studio Code, check that R is installed, add R support to VS Code, and test that R works in the VS Code terminal.

## 1. Open Install University Applications

1. Click the Windows search box, or press the Windows key.
2. Search for:

```text
Install University Applications
```

3. Open the application.

## 2. Install Visual Studio Code

1. In **Install University Applications**, use the search box at the top.
2. Search for:

```text
Visual Studio Code
```

3. Select **Visual Studio Code**.
4. Click **Install**.

The installation usually takes around **5 minutes**.

## 3. Check that R is installed

1. In **Install University Applications**, search for:

```text
R 4.5.2
```

2. If it says **Installed**, no further action is needed.
3. If it says **Available**, select it and click **Install**.

## 4. Open Visual Studio Code

1. Click the Windows search box, or press the Windows key.
2. Search for:

```text
Visual Studio Code
```

3. Open Visual Studio Code.

## 5. Install the R extension in VS Code

1. In VS Code, click the **Extensions** button in the left toolbar.

   It looks like four small blocks.

2. Alternatively, press:

```text
Ctrl + Shift + X
```

3. In the Extensions search box, search for:

```text
REditorSupport
```

4. Install the extension called **R** by **REditorSupport**.

### Why install this extension?

VS Code can open and edit R scripts without an extension, but the R extension makes it much better for R programming.

It adds useful features such as:

- R syntax highlighting
- better code completion
- tools for running R code from VS Code
- support for working with R scripts more comfortably
- integration with the R terminal

This makes VS Code behave more like a proper R coding environment rather than just a basic text editor.

## 6. Open PowerShell inside VS Code

In VS Code, go to:

```text
Terminal > New Terminal
```

A terminal panel should open at the bottom of VS Code.

This will usually open as **PowerShell**.

## 7. Test that R works

Copy and paste this command into the VS Code terminal:

```powershell
Remove-Item Alias:r -Force -ErrorAction SilentlyContinue; R --version
```

Then press **Enter**.

You should see version information for R, for example:

```text
R version 4.5.2
```

## What the command does

PowerShell has a built-in shortcut called `r`, which can interfere with running R from the terminal. PowerShell aliases are not case-sensitive, so `R` can be interpreted as the PowerShell `r` shortcut instead of the R program.

This part removes the PowerShell shortcut for the current terminal session:

```powershell
Remove-Item Alias:r -Force -ErrorAction SilentlyContinue
```

This part checks that R is installed and available:

```powershell
R --version
```

## 8. Start R in the VS Code terminal

After removing the alias, you can start R by typing:

```powershell
R
```

To exit R, type:

```r
q()
```

Then press **Enter**.

## 9. Add R to system PATH (if needed)

If R does not start when you type `R` in PowerShell, R may not be in your system PATH. Adding R to PATH allows you to run R from any terminal location.

### Find the R installation directory

1. Open File Explorer.
2. Navigate to:

```text
C:\Program Files\R
```

Look for a folder named `R-4.5.2` (or similar R version).

3. Inside this folder, confirm there is a `bin` directory.
4. Copy the full path, for example:

```text
C:\Program Files\R\R-4.5.2\bin
```

### Add R to system PATH

1. Click the Windows search box, or press the Windows key.
2. Search for:

```text
Edit the system environment variables
```

3. Click on **Environment Variables** button (bottom right of the dialog).

4. Under **User variables**, click **New**.

5. For **Variable name**, type:

```text
PATH
```

6. For **Variable value**, paste the R `bin` directory path you copied earlier:

```text
C:\Program Files\R\R-4.5.2\bin
```

7. Click **OK** and close all dialogs.

8. **Close and reopen PowerShell** in VS Code for the changes to take effect.

9. Test that R is now in PATH by typing:

```powershell
Remove-Item Alias:r -Force -ErrorAction SilentlyContinue; R --version
```

R should now launch successfully.
