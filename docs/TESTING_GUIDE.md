# Quick Start: Testing Multiple Emulator Instances

## What Was Fixed

The AVD cloning mechanism now creates **truly independent virtual devices** that can run simultaneously. Each clone has:
- ✅ Unique device identifiers
- ✅ Independent storage and cache
- ✅ No snapshot conflicts
- ✅ Full read-write access (no read-only mode)

## Quick Test (5 minutes)

### 1. Start the Application
```powershell
cd d:\Workspaces\GitHub\AndroidMulti
python main.py
```

### 2. Create Multiple Clones

1. Click **"➕ Create Emulator"**
2. Select your AVD template
3. **Check** "Create as clone"
4. Click **"Create & Start"**
5. Wait ~1 minute for it to boot
6. **Repeat 2-3 times** to create multiple instances

### 3. Test Input Sync

1. Check **"Enable Sync"** in the toolbar
2. Interact with any emulator window
3. Watch the input replicate across all instances! 🎉

## Expected Results

✅ All emulators start without errors  
✅ Each shows "Running" status with unique port  
✅ No "read-only" warnings in logs  
✅ Input syncs across all instances  

## If Something Goes Wrong

Check the **Logs** tab for detailed error messages. Common issues:
- **Clone fails:** Check disk space and AVD Manager path in Settings
- **Won't start:** Ensure hardware acceleration is enabled
- **Sync not working:** Wait for emulators to fully boot (status = "Running")

## Key Files Changed

- [`emulator_manager.py`](file:///d:/Workspaces/GitHub/AndroidMulti/src/emulator_manager.py) - Enhanced AVD cloning
- [`emulator_worker.py`](file:///d:/Workspaces/GitHub/AndroidMulti/src/gui/emulator_worker.py) - Better progress reporting

See [`walkthrough.md`](file:///C:/Users/jbeno/.gemini/antigravity/brain/0caf264d-559f-4c4c-a89f-07bd2e94899e/walkthrough.md) for complete documentation.
