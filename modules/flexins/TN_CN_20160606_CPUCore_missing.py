# -*- coding: utf-8 -*-
u"""
 检查FlexiNS CPU Blade是否存在丢核现象
    --
    --检查指令:
        ZDDE:OMU:"ZMA:W0,F3,,,,,","ZMA:W1,F3,,,,,","ZGSC:,00FC";

        如果磁盘碎片率大于60%,判断为偏高。
    --检查指令可能会对硬盘有影响，执行后，请检查硬盘状态。
        ZISI:,:WDU,;
    --如果出现磁盘碎片率偏高的现象，请按照TN-Flexi_NS-SW0013-CI2中介绍修复。
"""

import re,sys
sys.path.append("R:\\SmartChecker")
from libs.checker import ResultInfo
from libs.checker import CheckStatus
from libs.infocache import shareinfo
from libs.log_spliter import LogSpliter

## Mandatory variables 
##--------------------------------------------
module_id = 'NSTNCN_20160606'
tag       = ['flexins','china']
priority  = 'major'
name      = u"FlexiNS CPUBlade Core 核心数减少问题检查"
desc      = __doc__
criteria  = u"""
（1）检查MME版本为 ['N5','N6'] 或者更高版本。
（2）检查OMU，MCHU的硬盘碎片率是否大于60%。大于为FAILED，小于则为PASSED。
（3）如果log中没有相应的指令log，结果为UNKNOWN。
"""
result = ResultInfo(name,module_id=module_id,priority=priority)
error = ''


##--------------------------------------------
## Optional variables
target_version = ['N5','N6']    

check_commands = [
    ("ZWQO:CR;","show the NS packages information"),
    ('ZDDE:{@UNIT_ID}:"cat /proc/cpuinfo | grep processor",;',"show CPU info of all CPU blade"),
]
def process_num(block):
    num = 0
    pat = re.compile("processor")
    _processors=re.findall("processor\s+: \d{1,2}",''.join(block))
    
    return len(_processors)
     
def caculate_cpu_cores(logfile):
    log=LogSpliter(logfile=logfile)
    #log.load(logfile)
    unit_pat = re.compile("ZDDE:(\w+),(\d+)")
    
    core_nums = {}
    for blk in log.get_log("cpuinfo",fuzzy=True):
        _unit = unit_pat.findall(blk.command)
        if _unit:
            unit = "-".join(_unit[0])
        else:
            continue
        core_nums[unit] = process_num(blk.result)
        
    return core_nums

def check_version(target_version):
    version_status = (CheckStatus.VERSION_UNKNOWN,'')
    ns = shareinfo.get('ELEMENT')
    if not ns.version:
        version_status=(CheckStatus.VERSION_UNKNOWN,"No version info was found.")
    else:
        nsversion = ns.version['BU']
        if ns.match_version(target_version):
            version_status=(CheckStatus.VERSION_MATCHED, u"- NS version: %s, 本检查适用于此版本" % nsversion) 
        else:
            version_status=(CheckStatus.VERSION_UNMATCHED,u"- NS version: %s, 本检查不适用与此版本。" % nsversion)
    
    return version_status
##--------------------------------------------
## Mandatory function: run
##--------------------------------------------    
def run(logfile):
    status = CheckStatus.UNCHECKED 
    errmsg = []    
    # Check NS Version
    vstatus,msg = check_version(target_version)
    print "versom check:",vstatus,msg
    
    if vstatus == CheckStatus.VERSION_UNKNOWN:
        result.update(status=CheckStatus.UNKNOWN,info=[msg],error=error)
    
    elif vstatus== CheckStatus.VERSION_MATCHED:
        cpuinfo = caculate_cpu_cores(logfile)
        _msg = []

        for unit,corenum in cpuinfo.items():
            if corenum < 12:
                errmsg.append("- Blade %s only have %s cores, Some cores are missing. 部分核丢失" % (unit,corenum))
            else:
                _msg.append("- Blade %s have 12 cores" % unit)
                
        if len(errmsg) > 0:
            status=CheckStatus.FAILED
        else:
            status=CheckStatus.PASSED
            
        result.update(status=status,info=_msg,error=errmsg)
   
    elif vstatus == CheckStatus.VERSION_UNMATCHED:
        result.update(status=CheckStatus.PASSED,info=[msg],error=errmsg)
    
    #print result.data
    return result


if __name__ == "__main__":
    logfile = sys.argv[1]
    #print caculate_cpu_cores(logfile)
    run(logfile)