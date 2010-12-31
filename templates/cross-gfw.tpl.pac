${
    #Using Templite+
    _use_cernet_no_free_ip_proxy = _cernet_no_free_ip_proxy and _cernet_free_ip_list_length > 0
}$\
//for ie.
//javascript engine in ie is slow, so dont cross gfw by ie
function FindProxyForURLEx(url, host) {
    var _dnsDomainIs = function(a,b){return dnsDomainIs(a,b);}
    var _isInNet = function(a,b,c){return isInNet(a,b,c);}
    var i = 0;
    var ips = '';
${for proxy_name in _proxy_names:}$\
${
        proxy_value = _lists['proxy'][proxy_name]
        if proxy_name=='_gfw_proxy' or proxy_value is None:
            continue
        hosts = '['+','.join(_lists['hosts'][proxy_name])+']'
        hosts_length = len(_lists['hosts'][proxy_name])
        nets = '['+','.join(_lists['nets'][proxy_name])+']'
        nets_length = len(_lists['nets'][proxy_name])
}$\
${if hosts_length > 0:}$\
    var ${proxy_name}$_hosts = ${hosts}$;
    for(i=${hosts_length}$; i--;)
        if(_dnsDomainIs(host, ${proxy_name}$_hosts[i]))
            return ${proxy_value}$;
${:endif}$\
${if nets_length > 0:}$\
    var ${proxy_name}$_nets = ${nets}$;
    for(i=${nets_length}$; i--;)
        if(_isInNet(host, ${proxy_name}$_nets[i][0], ${proxy_name}$_nets[i][1]))
            return ${proxy_value}$;
${:endif}$\
${:end-for}$\
${if _ipv6_proxy:}$\
    //for ipv6
    ips = dnsResolveEx(host);
    if (shExpMatch(ips, "*:*"))
        return ${_ipv6_proxy}$;
${:endif}$\
${if _use_cernet_no_free_ip_proxy:}$\
    //for cernet no free ip
    for(i=${_cernet_free_ip_list_length}$; i--;)
        if(_isInNet(host, _cernet_free_ip_list[i][0], _cernet_free_ip_list[i][1]))
            return ${_normal_proxy}$;
${:endif}$\
${if _use_cernet_no_free_ip_proxy:}$\
    return ${_cernet_no_free_ip_proxy}$;
${:else:}$\
    return ${_normal_proxy}$;
${:endif}$\
}
function FindProxyForURL(url, host) {
    var _dnsDomainIs = dnsDomainIs;
    var _isInNet = isInNet;
    var i = 0;
    var ips = '';
${for proxy_name in _proxy_names:}$\
${
        proxy_value = _lists['proxy'][proxy_name]
        if proxy_value is None:
            continue
        hosts = '['+','.join(_lists['hosts'][proxy_name])+']'
        hosts_length = len(_lists['hosts'][proxy_name])
        nets = '['+','.join(_lists['nets'][proxy_name])+']'
        nets_length = len(_lists['nets'][proxy_name])
}$\
${if hosts_length > 0:}$\
    var ${proxy_name}$_hosts = ${hosts}$;
    for(i=${hosts_length}$; i--;)
        if(_dnsDomainIs(host, ${proxy_name}$_hosts[i]))
            return ${proxy_value}$;
${:endif}$\
${if nets_length > 0:}$\
    var ${proxy_name}$_nets = ${nets}$;
    for(i=${nets_length}$; i--;)
        if(_isInNet(host, ${proxy_name}$_nets[i][0], ${proxy_name}$_nets[i][1]))
            return ${proxy_value}$;
${:endif}$\
${:end-for}$\
${if _ipv6_proxy:}$\
    //for ipv6
    if(typeof(dnsResolveEx) == 'function')
        ips = dnsResolveEx(host);
    else
        ips = dnsResolve(host);
    if (shExpMatch(ips, "*:*"))
        return ${_ipv6_proxy}$;
${:endif}$\
${if _use_cernet_no_free_ip_proxy:}$\
    //for cernet no free ip
    for(i=${_cernet_free_ip_list_length}$; i--;)
        if(_isInNet(host, _cernet_free_ip_list[i][0], _cernet_free_ip_list[i][1]))
            return ${_normal_proxy}$;
${:endif}$\
${if _gfw_proxy:}$\
    //cross gfw
    if(isBlockedByGFW(url, host))
        return ${_gfw_proxy}$;
${:endif}$\
${if _use_cernet_no_free_ip_proxy:}$\
    return ${_cernet_no_free_ip_proxy}$;
${:else:}$\
    return ${_normal_proxy}$;
${:endif}$\
}
${if _gfw_proxy:}$\
${
    _gfw_http_list = '[\''+'\',\''.join(_gfwlist['http'])+'\']'
    _gfw_https_list = '[\''+'\',\''.join(_gfwlist['https'])+'\']'
    _gfw_regexp_list = '['+','.join(_gfwlist['regexp'])+']'
    _gfw_domain_list = '[\''+'\',\''.join(_gfwlist['domain'])+'\']'
    _gfw_keyword_list = '[\''+'\',\''.join(_gfwlist['keyword'])+'\']'
    _ignore_gfw_http_list = '[\''+'\',\''.join(_gfwlist['ignore']['http'])+'\']'
    _ignore_gfw_https_list = '[\''+'\',\''.join(_gfwlist['ignore']['https'])+'\']'
    _ignore_gfw_regexp_list = '['+','.join(_gfwlist['ignore']['regexp'])+']'
    _ignore_gfw_domain_list = '[\''+'\',\''.join(_gfwlist['ignore']['domain'])+'\']'
    _ignore_gfw_keyword_list = '[\''+'\',\''.join(_gfwlist['ignore']['keyword'])+'\']'
    
    _gfw_http_list_length = len(_gfwlist['http'])
    _gfw_https_list_length = len(_gfwlist['https'])
    _gfw_regexp_list_length = len(_gfwlist['regexp'])
    _gfw_domain_list_length = len(_gfwlist['domain'])
    _gfw_keyword_list_length = len(_gfwlist['keyword'])
    _ignore_gfw_http_list_length = len(_gfwlist['ignore']['http'])
    _ignore_gfw_https_list_length = len(_gfwlist['ignore']['https'])
    _ignore_gfw_regexp_list_length = len(_gfwlist['ignore']['regexp'])
    _ignore_gfw_domain_list_length = len(_gfwlist['ignore']['domain'])
    _ignore_gfw_keyword_list_length = len(_gfwlist['ignore']['keyword'])
}$
function isBlockedByGFW(url, host) {
    var i = 0;
    var proto = url.substr(0, 5);
    var _shExpMatch = shExpMatch;
    var _dnsDomainIs = dnsDomainIs;
    if(proto == 'http:') {
${if _ignore_gfw_http_list_length > 0:}$\
        var _ignore_http_list = ${_ignore_gfw_http_list}$;
        for(i=${_ignore_gfw_http_list_length}$; i--;)
            if(_shExpMatch(url, _ignore_http_list[i]+'*'))
                return false;
${:endif}$\
${if _gfw_http_list_length > 0:}$\
        var _http_list = ${_gfw_http_list}$;
        for(i=${_gfw_http_list_length}$; i--;)
            if(_shExpMatch(url, _http_list[i]+'*'))
                return true;
${:endif}$\
    }
    else if(proto == 'https') {
${if _ignore_gfw_https_list_length > 0:}$\
        var _ignore_https_list = ${_ignore_gfw_https_list}$;
        for(i=${_ignore_gfw_https_list_length}$; i--;)
            if(_shExpMatch(url, _ignore_https_list[i]+'*'))
                return false;
${:endif}$\
${if _gfw_https_list_length > 0:}$\
        var _https_list = ${_gfw_https_list}$;
        for(i=${_gfw_https_list_length}$; i--;)
            if(_shExpMatch(url, _https_list[i]+'*'))
                return true;
${:endif}$\
    }
${if _ignore_gfw_regexp_list_length > 0:}$\
    var _ignore_regexp_list = ${_ignore_gfw_regexp_list}$;
    for(i=${_ignore_gfw_regexp_list_length}$; i--;)
        if(_ignore_regexp_list[i].test(url)) 
            return false;
${:endif}$\
${if _gfw_regexp_list_length > 0:}$\
    var _regexp_list = ${_gfw_regexp_list}$;
    for(i=${_gfw_regexp_list_length}$; i--;) 
        if(_regexp_list[i].test(url)) 
            return true;
${:endif}$\
${if _ignore_gfw_domain_list_length > 0:}$\
    var _ignore_domain_list = ${_ignore_gfw_domain_list}$;
    for(i=${_ignore_gfw_domain_list_length}$; i--;)
        if(_dnsDomainIs(host, _ignore_domain_list[i]))
            return false;
${:endif}$\
${if _gfw_domain_list_length > 0:}$\
    var _domain_list = ${_gfw_domain_list}$;
    for(i=${_gfw_domain_list_length}$; i--;)
        if(_dnsDomainIs(host, _domain_list[i]))
            return true;
${:endif}$\
${if _ignore_gfw_keyword_list_length > 0:}$\
    var _ignore_keyword_list = ${_ignore_gfw_keyword_list}$;
    for(i=${_ignore_gfw_keyword_list_length}$; i--;)
        if(_shExpMatch(url, _ignore_keyword_list[i]+'*'))
            return false;
${:endif}$\
${if _gfw_domain_list_length > 0:}$\
    var _keyword_list = ${_gfw_keyword_list}$;
    for(i=${_gfw_keyword_list_length}$; i--;)
        if(_shExpMatch(url, '*'+_keyword_list[i]+'*'))
            return true;
${:endif}$\
    return false;
}
${:endif}$