// Capacity experiment, not a claim about native phone recognition.
const QRCode=require('qrcode');
for(const text of ['HTTPS://PAC.S.GY/ABCDEFGH','pac.s.gy/ABCDEFGH','PAC.S.GY/ABCDEFGH','https://pac.s.gy/ABCDEFGH','https://PAC.S.GY/ABC','https://PAC.S.GY/ABCD','http://PAC.S.GY/ABCDE','https://pac.s.gy/A','https://p.s.gy/AB']) {
  for(const mode of ['auto','byte']) {
    const qr=QRCode.create(mode==='auto'?text:[{data:text,mode}],{errorCorrectionLevel:'L'});
    console.log(JSON.stringify({text,mode,version:qr.version,size:qr.modules.size,segments:qr.segments.map(x=>x.mode.id)}));
  }
}
