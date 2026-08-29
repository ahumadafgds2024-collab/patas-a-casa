from pathlib import Path
import re

path = Path('mi-cuenta/index.html')
html = path.read_text(encoding='utf-8')

style = r'''<style id="pac-brand-colors-v1">
:root{
  --pac-teal:#0a7f83;
  --pac-teal-dark:#086b70;
  --pac-orange-brand:#ff641f;
  --pac-teal-soft:rgba(10,127,131,.075);
  --pac-orange-soft:rgba(255,100,31,.085);
}
body{
  background:
    radial-gradient(circle at 9% -5%,rgba(255,100,31,.115),transparent 27%),
    radial-gradient(circle at 96% 18%,rgba(10,127,131,.095),transparent 23%),
    linear-gradient(180deg,#faf7f2 0,var(--pac-bg) 52%,#f3ede5 100%)!important;
}
.account-overview .kicker{color:var(--pac-teal-dark)!important}
.add-tag-btn{
  background:var(--pac-orange-soft)!important;
  border:1px solid rgba(255,100,31,.15)!important;
  color:#302a26!important;
}
.add-tag-btn .ui-icon{color:var(--pac-orange-brand)!important;stroke-width:2.1}
.community-card{
  background:linear-gradient(135deg,rgba(10,127,131,.065),rgba(255,253,250,.88))!important;
  border-color:rgba(10,127,131,.15)!important;
}
.community-link{color:#2d2a27!important}
.community-link .ui-icon,.community-arrow{color:var(--pac-teal)!important}
.community-link:active{background:rgba(10,127,131,.075)!important}
.quiet .ui-icon,.recovery .ui-icon{color:var(--pac-teal)!important;stroke-width:2}
.quiet:active{background:rgba(10,127,131,.055)!important}
.recovery{background:rgba(10,127,131,.055)!important;border-color:rgba(10,127,131,.105)!important}
.pet-more summary{color:#66615c!important}
.pet-more summary .ui-icon{display:none!important}
.pet-more summary::after{
  content:'⌄';
  color:var(--pac-teal);
  font-size:20px;
  font-weight:800;
  line-height:1;
  margin-left:1px;
  transform:translateY(-1px);
}
.pet-more[open] summary::after{content:'⌃';transform:translateY(1px)}
.pet-more[open] summary{color:#403c38!important}
.tag-code{color:#716b65!important}
.header-menu{color:var(--pac-teal-dark)!important}
.quick-access-card h2{color:#252321}
@media (prefers-contrast:more){
  .tag-code{color:#514c47!important}
  .community-card{border-color:rgba(10,127,131,.3)!important}
}
</style>'''

html = re.sub(r'\n?<style id="pac-brand-colors-v1">.*?</style>', '', html, flags=re.S)
if '</head>' not in html:
    raise SystemExit('No se encontró </head>')
html = html.replace('</head>', style + '\n</head>', 1)
path.write_text(html, encoding='utf-8')
print('Colores de marca aplicados al panel.')
