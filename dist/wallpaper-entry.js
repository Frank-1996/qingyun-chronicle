const host = location.hostname;
if (host === 'a.qingyunlife.cn' || host === 'qingyun-chronicle.vercel.app') {
  location.replace('./game.html' + location.search + location.hash);
}
