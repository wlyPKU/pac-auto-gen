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
    proxy = pacproxy.lower().strip('"\'')
    if proxy.startswith('direct'):
        return None
    if proxy.startswith('proxy'):
        return [('http', proxy.replace('proxy ', 'http://')),
                ('https', proxy.replace('proxy ', 'http://'))]
    if proxy.startswith('socks'):
        return [('socks', proxy.replace('socks ', 'http://'))]
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
        except IOError, e:
            raise ReadFileError(url)
        else:
            if content:
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
        self._logger.info("fetch page `%s` through proxy `%s` successfully", url, pacproxy)
        return page

    def _write_hosts(self):
        page = self._fetch(self._config['ipv6-host-file-url'], self._config['ipv6-host-file-proxy'])
        fp = open(self._config['system-host-file-path'], 'w')
        lines = page.split('\n')
        for line in lines:
            line = line.strip()
            if line == '':
                continue
            if line[0] == '#':
                continue
            if not line[0].isdigit() and not line[0] == ':':
                continue
            print >>fp, line
        fp.write("\n")
        fp.write(self._config['my-hosts'])
        fp.close()
        self._logger.info("write hosts file `%s` successfully", self._config['system-host-file-path'])
    

    def _init_gfw(self):
        page = self._fetch(self._config['gfw-list-file-url'], self._config['gfw-list-file-proxy'])
        autoproxy_list = base64.decodestring(page).split("\n")
        gfw_list = []
        gfw_regexp_list = []
        gfw_http_list = []
        gfw_https_list = []
        for line in autoproxy_list[1:]:
            line = line.strip(' +*')
            if line == '' or line[0] == '!' or line.startswith('@@'):
                continue
            if line.startswith('||'):
                continue
            if line[0] == '|':
                line = line[1:]
                if line.startswith('http:'):
                    gfw_http_list.append(line)
                elif line.startswith('https:'):
                    gfw_https_list.append(line)
            elif line[0] == '.':
                gfw_list.append(line[1:])
            else:
                if line[0]=='/' and line[-1] =='/':
                    gfw_regexp_list.append(line)
                    continue
                if line[-1] == '|':
                    line = line[:-1]
                gfw_list.append(line)
        self._vars['_gfw_proxy'] = self._config['gfw-proxy']
        self._vars['_gfw_list'] = "['"+"','".join(gfw_list)+"']"
        self._vars['_gfw_regexp_list'] = "["+",".join(gfw_regexp_list)+"]"
        self._vars['_gfw_http_list'] = "['"+"','".join(gfw_http_list)+"']"
        self._vars['_gfw_https_list'] = "['"+"','".join(gfw_https_list)+"']"
        self._vars['_gfw_list_length'] = len(gfw_list)
        self._vars['_gfw_regexp_list_length'] = len(gfw_regexp_list)
        self._vars['_gfw_http_list_length'] = len(gfw_http_list)
        self._vars['_gfw_https_list_length'] = len(gfw_https_list)

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

