from pathlib import Path

path = Path('mi-cuenta/index.html')
s = path.read_text(encoding='utf-8')
old = '''function showInstallFinish(installed=false){
 if(isStandalone()){setInstallPending(false);clearIosSessionBridge();loadDashboard();return}
 setInstallPending(true);if(isiOS())writeIosSessionBridge();
 const ios=isiOS();'''
new = '''function showInstallFinish(installed=false){
 if(isStandalone()){setInstallPending(false);clearIosSessionBridge();loadDashboard();return}
 if(!installed){setInstallPending(true);if(isiOS())writeIosSessionBridge()}else setInstallPending(false);
 const ios=isiOS();'''
if old not in s:
    raise SystemExit('No encontré showInstallFinish en el formato esperado')
s = s.replace(old, new, 1)
path.write_text(s, encoding='utf-8')
print('OK: estado de instalación final corregido')
