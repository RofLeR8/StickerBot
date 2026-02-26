# Logging Configuration

## Overview
Comprehensive logging has been added to the StickerBot application to help diagnose issues, particularly the "стикер утерян" (sticker lost) error.

## Configuration

### Environment Variable
Set the log level using the `LOG_LEVEL` environment variable:
- `DEBUG` - Detailed debugging information
- `INFO` - General operational messages (default)
- `WARNING` - Warning messages
- `ERROR` - Error messages
- `CRITICAL` - Critical errors

### Docker
The Dockerfile sets `LOG_LEVEL=INFO` by default. Override it when running the container:
```bash
docker run -e LOG_LEVEL=DEBUG ...
```

### Local Development
Set the environment variable before running:
```bash
export LOG_LEVEL=DEBUG
python src/main.py --mode dev
```

## Log Format
```
YYYY-MM-DD HH:MM:SS | LEVEL    | module:line | Message
```

Example:
```
2026-02-26 10:30:45 | INFO     | main:65 | Starting bot in mode: dev
2026-02-26 10:30:46 | INFO     | handlers.sticker_add:52 | User 12345: attempting to add sticker
```

## Key Log Points for "Sticker Lost" Error

The following log messages will help identify why the "стикер утерян" error occurs:

1. **Photo/Sticker Received**
   - `User {id} sent photo for sticker creation`
   - `User {id}: photo file_id={id}, file_size={size}`
   - `User {id}: photo downloaded to {path}`

2. **State Management**
   - `User {id}: state set to choose_option`
   - `User {id}: temp_photo_path from state={path}`

3. **File Processing**
   - `User {id}: processing image to {path}`
   - `User {id}: image resized`
   - `User {id}: sticker_path saved to state: {path}`

4. **Critical Check** (where the error occurs)
   - `User {id}: sticker_path={path}, exists={True/False}`
   - `User {id}: sticker file not found at {path} - THIS IS THE ERROR!`

## Common Causes for "Sticker Lost" Error

Based on the logging, look for:

1. **File not found after state transition**
   - Check if `temp_photo_path` exists in state
   - Verify `PHOTO_DIR` directory is writable

2. **File deleted prematurely**
   - Check cleanup operations in `/cancel` command
   - Verify file isn't being deleted by external processes

3. **Permission issues**
   - Check Docker volume mounts for `/app/data/photos`
   - Verify `appuser` has write permissions

4. **State cleared before completion**
   - Check for unexpected state clears
   - Verify FSM state persistence

## Viewing Logs in Docker

```bash
# View live logs
docker logs -f <container_name>

# View last 100 lines
docker logs --tail 100 <container_name>

# Search for errors
docker logs <container_name> | grep -i error
```

## Files with Logging

- `src/logging_config.py` - Central logging configuration
- `src/main.py` - Bot startup and initialization
- `src/handlers/sticker_add.py` - Sticker creation flow (most detailed)
- `src/handlers/sticker_delete.py` - Sticker deletion flow
- `src/handlers/start.py` - Start command handler
- `src/handlers/admin.py` - Admin panel
- `src/handlers/register.py` - User registration
- `src/database/crud.py` - Database operations
- `src/database/database.py` - Database connection
- `src/image/utils.py` - Image processing
- `src/middlewares/middleware.py` - Database session middleware
