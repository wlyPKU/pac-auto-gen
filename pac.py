#!/usr/bin/env python
import urllib
import re
import base64
import ConfigParser
from templite import Templite
import logging
import os
import os.path
import traceback
import sys 

class Configure(ConfigParser.ConfigParser):
    __defaults__ = {
        'direct-proxy':'"DIRECT"',
        'normal-proxy':'"DIRECT"',
        
        'pac-directory':'pacfiles',
        'log-file':'log.txt',
        
        'write-host-file':'Off',
        'ipv6-host-file-url':'http://docs.google.com/MiscCommands?command=saveasdoc&docID=0ARhAbsvps1PlZGZrZG14bnRfNjFkOWNrOWZmcQ&exportFormat=txt',
        'ipv6-host-file-proxy':'"DIRECT"',
        'system-host-file-path':r'C:\WINDOWS\system32\drivers\etc\hosts',
        'my-hosts':'',

        'gfw-list-file-url':'http://autoproxy-gfwlist.googlecode.com/svn/trunk/gfwlist.txt',
        'gfw-list-file-proxy':'"DIRECT"',

        'cernet-free-ip-list-url':'http://www.nic.edu.cn/RS/ipstat/internalip/real.html',
        'cernet-free-ip-list-proxy':'"DIRECT"'
    }

    def __init__(self, file):
        ConfigParser.ConfigParser.__init__(self)
        self.read(file)

    def __getitem__(self, option):
        try:
            return self.get('Pac', option)
        except ConfigParser.NoOptionError, e:
            if self.__class__.__defaults__.has_key(option):
                return self.__class__.__defaults__[option]
            return None
        except ConfigParser.InterpolationError, e:
            return None

def urlproxy(pacproxy):
    proxy_str = pacproxy.lower().strip('"\'')
    proxies = proxy_str.split(';')
    for proxy in proxies:
        proxy = proxy.strip()
        if proxy.startswith('direct'):
            return None
        if proxy.startswith('proxy'):
            return [('http', proxy.replace('proxy ', 'http://')),
                    ('https', proxy.replace('proxy ', 'http://'))]
        #if proxy.startswith('socks'):
            #return [('socks', proxy.replace('socks ', 'http://'))]
    return None

class Error(Exception):
    pass

class FetchError(Error):
    
    def __init__(self, url, proxy):
        self.url = url
        self.proxy = proxy

    def __str__(self):
        return "failed to fetch page `%s` through proxy `%s`" % (self.url, self.proxy)

class ReadFileError(Error):
    
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return "failed to read file `%s`" % (self.path)

class Pac:
    
    def __init__(self, configfile):
        
        self._config = Configure(configfile)
        self._vars = {}
        self._host_pattern = re.compile(r'[\'"][^\'",]+[\'"]')
        self._net_pattern = re.compile(r'\[[\'"][^\'",]+[\'"],\s*[\'"][^\'",]+[\'"]\]')
        logging.basicConfig(filename=self._config['log-file'], level=logging.DEBUG, 
            format="[%(asctime)-15s]%(levelname)s:%(message)s")
        self._logger = logging

    def _fetch(self, url, pacproxy='"DIRECT"'):
        try:
            content = None
            if url.find("://") < 0:
                content = open(url).read()
            if url.startswith("file://"):
                content = open(url[7:]).read()
        except Error, e:
            raise ReadFileError(url)
        else:
            if content is not None:
                self._logger.info("read file `%s` successfully", url)
                return content

        return self._webfetch(url, pacproxy)
    
    def _webfetch(self, url, pacproxy):

        proxy = urlproxy(pacproxy)
        try:
            if proxy:
                web = urllib.FancyURLopener(dict(proxy))
            else:
                web = urllib.FancyURLopener()
            page = web.open(url).read()
        except:
            raise FetchError(url, pacproxy)
        finally:
            web.close()
        if page == '':
            self._logger.warning("fetch page `%s` through proxy `%s` successfully, but it is empty", url, pacproxy)
        else:
            self._logger.info("fetch page `%s` through proxy `%s` successfully", url, pacproxy)
        return page

    def _write_hosts(self):
        page = self._fetch(self._config['ipv6-host-file-url'], self._config['ipv6-host-file-proxy'])
        lines = page.split('\n')
        hosts = []
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            if line[0] == '#':
                continue
            if not line[0].isdigit() and not line[0] == ':':
                continue
            hosts.append(line)
        if len(hosts) == 0:
            self._logger.warning("`%s` is empty, there is no host record in it", self._config['ipv6-host-file-url'])
        fp = open(self._config['system-host-file-path'], 'w')
        print >>fp, "\n".join(hosts)
        fp.write("\n")
        fp.write(self._config['my-hosts'])
        fp.close()
        self._logger.info("write hosts file `%s` successfully", self._config['system-host-file-path'])
    
    def _parse_rule(self, rule):
        if rule[-1] == '|':
            rule = rule[:-1]
        #if rule[0] == '.':
            #rule = rule[1:]
        if rule.startswith('||'):
            r = rule[2:].strip('/')
            p = r.find('/')
            if p > 0:
                r = r[:p]
            return ('domain', r)
        if rule[0] == '|':
            if rule.startswith('|http:'):
                return ('http', rule[1:])
            elif rule.startswith('|https:'):
                return ('https', rule[1:])
        if rule[0] == '/' and rule[-1] == '/':
            return ('regexp', rule)
        return ('keyword', rule)

    def _init_gfw(self):
        page = self._fetch(self._config['gfw-list-file-url'], self._config['gfw-list-file-proxy'])
        autoproxy_rules = base64.decodestring(page).split("\n")
        gfwlist = {'keyword':[], 'domain':[], 'regexp':[], 'http':[], 'https':[], 'ignore':{}}
        for key in gfwlist.keys():
            if key == 'ignore':
                continue
            gfwlist['ignore'][key] = []
        for line in autoproxy_rules[1:]:
            line = line.strip(' +*')
            if line == '' or line[0] == '!':
                continue
            if line.startswith('@@'):
                type, element = self._parse_rule(line[2:])
                gfwlist['ignore'][type].append(element)
                continue
            type, element = self._parse_rule(line)
            gfwlist[type].append(element)
        
        for key in gfwlist.keys():
            if key == 'ignore':
                continue
            gfwlist[key] = list(set(gfwlist[key]))
            gfwlist['ignore'][key] = list(set(gfwlist['ignore'][key]))
            
        self._vars['_gfw_proxy'] = self._config['gfw-proxy']
        self._vars['_gfwlist'] = gfwlist

    def _init_cernet(self):
        page = self._fetch(self._config['cernet-free-ip-list-url'],
                    self._config['cernet-free-ip-list-proxy'])
        lines = page.split("\n")
        free_ip_list = []
        for line in lines:
            match = re.match(r'([0-9\.]+)\s+[0-9\.]+\s+([0-9\.]+)\s*', line)
            if match:
                free_ip_list.append("['%s','%s']" % (match.group(1), match.group(2)))
        self._vars['_cernet_free_ip_list'] = "["+ ",".join(free_ip_list)+"]"
        self._vars['_cernet_free_ip_list_length'] = len(free_ip_list)
        if len(free_ip_list) == 0:
            self._logger.warning("cernet free ip list is empty, content of `%s`:\n%s\n", 
                self._config['cernet-free-ip-list-url'], page)
    
    def _get_config(self, var_name):
        key = var_name.replace('_', '-')
        return self._config[key[1:]]
    
    def _array_list(self, array_name, type):
        arraystr = self._get_config(array_name)
        if arraystr is None:
            return []
        if type=='hosts':
            return self._host_pattern.findall(arraystr)
        else:
            return self._net_pattern.findall(arraystr)
   
    def _init_common(self):
        proxy_names = ['direct', 'normal', 'ipv6', 'gfw', 'cernet_no_free_ip']
        self._vars['_proxy_names'] = ['_'+proxy+'_proxy' for proxy in proxy_names]
        self._vars['_lists'] = {'proxy':{}, 'hosts':{}, 'nets':{}}
        
        proxy_names = self._vars['_proxy_names']
        proxy_list = self._vars['_lists']['proxy']
        hosts_list = self._vars['_lists']['hosts']
        nets_list = self._vars['_lists']['nets']
        for i in range(len(proxy_names)):
            proxy = proxy_names[i]
            proxy_value = self._get_config(proxy)
            proxy_list[proxy] = proxy_value 
            self._vars[proxy] = proxy_value
            hosts_list[proxy] = self._array_list(proxy+'_hosts', 'hosts')
            nets_list[proxy] = self._array_list(proxy+'_nets', 'nets')
            if proxy_value is None:
                continue
            for j in range(i):
                if proxy_value != proxy_list[proxy_names[j]]:
                    continue
                hosts_list[proxy_names[j]].extend(hosts_list[proxy])
                nets_list[proxy_names[j]].extend(nets_list[proxy])
                del hosts_list[proxy][:]
                del nets_list[proxy][:]
                break
    
    def _init_vars(self):
        self._init_common()
        if self._config['ipv6-proxy'] is not None and \
            self._config['write-host-file'].lower() == 'on':
            self._write_hosts()
        if self._config['gfw-proxy'] is not None:
            self._init_gfw()
        if self._config['cernet-no-free-ip-proxy'] is not None:
            self._init_cernet()
    
    def _write_pac(self):
        files = os.listdir('templates')
        templates = []
        for file in files:
            if file.endswith('.tpl.pac'):
                templates.append(file)
        dir = self._config['pac-directory'].strip('\'"')
        if not dir.endswith(os.sep):
            dir = dir + os.sep
        if not os.path.exists(dir):
            os.makedirs(dir)
            self._logger.info("directory `%s` does not exist, create it", dir)
        for template_file in templates:
            template = self._fetch("templates"+os.sep+template_file).replace("\r\n", "\n")
            t = Templite(template)
            path = dir + template_file.replace('.tpl', '')
            open(path, 'w').write(t.render(self._vars).replace("\\\n",""))
            self._logger.info("write pac file `%s` successfully", path)
    
    def gen(self):
        try:
            self._init_vars()
            self._write_pac()
        except Error, e:
            self._logger.error(e)
        except Exception, e:
            p = traceback.format_exc()
            self._logger.error(p)

if __name__ == "__main__":
    if not os.path.isfile('pac.ini'):
        print "Please rename pac.example.ini to pac.ini before you run this program"
        raw_input('Hit ENTER to exit.')
    else:
        pac = Pac('pac.ini')
        pac.gen()

