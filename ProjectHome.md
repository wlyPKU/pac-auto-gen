使用本程序请阅读[README](https://code.google.com/p/pac-auto-gen/wiki/README)

## 关于本程序 ##

学校内部上网情况比较复杂，有IPv6网站，有教育网非免费网站，有被墙的网站，可能涉及到很多的代理，目前在firefox下和chrome下有很多的插件可以手动设置一些规则进行判断，但是这个设置和切换比较麻烦。

编写一个Pac文件自动判断如何选择代理上网可能更方便一些，本人之前尝试过，用的还不错，不过后来发现手动编写的Pac文件经常会过时，因为新的IPv6网站一直在加入，被墙网站总在变化，教育网免费网站经常增加减少，所以就用Python编写了一个自动更新Pac文件的小程序，希望对其他人也有帮助。

如果有什么问题，可以联系作者 liangqing226 AT gmail


感谢[autoproxy-gfwlist](https://code.google.com/p/autoproxy-gfwlist/)项目维护的gfwlist


感谢冰临宸夏维护的[IPv6 hosts列表](https://docs.google.com/Doc?docid=0ARhAbsvps1PlZGZrZG14bnRfNjFkOWNrOWZmcQ&hl=zh_CN)