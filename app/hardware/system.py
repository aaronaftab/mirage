import logging
import subprocess
import psutil
from typing import Dict, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class SystemHardware:
    """Hardware interface for the Raspberry Pi system"""
    
    def __init__(self, service_name: str = 'mirage'):
        self.service_name = service_name
    
    def run_command(self, command: list[str], timeout: int = 10) -> Tuple[bool, str]:
        """Run a system command and return success status and output"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            return success, output.strip()
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except Exception as e:
            return False, str(e)
    
    def get_temperature(self) -> Optional[float]:
        """Get CPU temperature using system file or vcgencmd"""
        try:
            # Try reading from system file first
            temp = Path('/sys/class/thermal/thermal_zone0/temp').read_text()
            return float(temp) / 1000.0
        except Exception as e:
            try:
                # Fallback to vcgencmd
                success, output = self.run_command(['vcgencmd', 'measure_temp'])
                if success:
                    # Parse output like "temp=45.8'C"
                    temp = output.replace('temp=', '').replace('\'C', '')
                    return float(temp)
            except Exception as e2:
                logger.error(f"Failed to read CPU temperature: {e2}")
                return None
    
    def get_system_stats(self) -> Dict:
        """Get comprehensive system statistics"""
        try:
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            stats = {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "temperature": self.get_temperature(),
                    "frequency": psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else None
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "swap_percent": psutil.swap_memory().percent
                },
                "disk": {
                    "total": disk.total,
                    "free": disk.free,
                    "percent": disk.percent
                }
            }
            
            logger.debug(f"System stats collected: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {disk.percent}%")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to collect system stats: {e}", exc_info=True)
            return {}
    
    def get_service_status(self) -> Dict:
        """Get status of the service"""
        success, output = self.run_command(['systemctl', 'status', self.service_name])
        
        status = {
            "active": False,
            "state": "unknown",
            "details": output
        }
        
        if success:
            for line in output.split('\n'):
                if 'Active:' in line:
                    status["state"] = line.split(':', 1)[1].strip()
                    status["active"] = 'active (running)' in line.lower()
                    break
        
        return status
    
    def control_service(self, action: str) -> Tuple[bool, str]:
        """Control the service (start/stop/restart)"""
        if action not in ['start', 'stop', 'restart']:
            raise ValueError(f"Invalid service action: {action}")
            
        logger.warning(f"Service {action} requested")
        return self.run_command(['sudo', 'systemctl', action, self.service_name])
    
    def control_power(self, action: str) -> Tuple[bool, str]:
        """Control system power (shutdown/reboot)"""
        if action not in ['shutdown', 'reboot']:
            raise ValueError(f"Invalid power action: {action}")
            
        logger.warning(f"System {action} requested")
        
        command = {
            'shutdown': ['sudo', 'shutdown', '-h', 'now'],
            'reboot': ['sudo', 'shutdown', '-r', 'now']
        }[action]
        
        return self.run_command(command) 