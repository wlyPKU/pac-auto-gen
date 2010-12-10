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
${if _use_cernet_no_free_ip_proxy:}$\
    return ${_cernet_no_free_ip_proxy}$;
${:else:}$\
    return ${_normal_proxy}$;
${:endif}$\
}