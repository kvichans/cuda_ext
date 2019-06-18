''' Lib for Plugin
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.9.01 2019-03-28'
Content
    log                 Logger with timing and code location
    _                   i18n
    get_hist,set_hist   Read|write from|to "*.json" a value by string key or path
ToDo: (see end of file)
'''

import  sys, os, gettext, logging, inspect, collections, json, re, subprocess
from    time        import perf_counter
from    functools   import lru_cache

import  cudatext        as app
from    cudatext    import ed
import  cudax_lib       as apx

VERSION     = re.split('Version:', __doc__)[1].split("'")[1]
VERSION_V,  \
VERSION_D   = VERSION.split(' ')

def version():  return VERSION_V

T,F,N       = True, False, None
C13,C10,C9  = chr(13),chr(10),chr(9)
def f(     s, *args, **kwargs): return       s.format(*args, **kwargs)
def printf(s, *args, **kwargs): return print(s.format(*args, **kwargs))

odict       = collections.OrderedDict
class odct(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        pass;                  #print('args=',args)
        if     args: super().__init__( *args) \
            if 1==len(args) else \
                     super().__init__(  args)
        elif kwargs: super().__init__(kwargs.items())
    def __str__(self):
        return '{%s}' % (', '.join("'%s': %r" % (k,v) for k,v in self.items()))
    def __repr__(self):
        return self.__str__()


#########################
#NOTE: log utility
#########################
LOG_FREE    = 0                                                 # No order (=False)
LOG_ALLOW   = 1                                                 # Allowed one (=True)
LOG_NEED    = 2                                                 # Required all
LOG_FORBID  = 3                                                 # Forbidden all
def iflog(*log_levels):
    " Get permission to log on multiple orders"
    if 2==len(log_levels):
        l1,l2   = log_levels
        if      l1==LOG_FORBID  or l2==LOG_FORBID:      return False  # If at least one is FORBID
        if      l1==LOG_NEED    or l2==LOG_NEED:        return True   # If at least one is NEED 
        return  l1==LOG_ALLOW   or l2==LOG_ALLOW                      # If at least one is ALLOW
    if      any([LOG_FORBID  ==l for l in log_levels]): return False  # If at least one is FORBID
    if      any([LOG_NEED    ==l for l in log_levels]): return True   # If at least one is NEED 
    return  any([LOG_ALLOW   ==l for l in log_levels])                # If at least one is ALLOW
   #def iflog

pass;                           _log4mod = LOG_FREE             # Order log in the module


def log__(msg='', *args, **kwargs):
    cond4log    = kwargs.pop('__', None) if kwargs else None
    if not cond4log or not iflog(*cond4log):    return 
    if args or kwargs:
        msg = msg.format(*args, **kwargs)
    if Tr.tr is None:
        Tr.tr=Tr()
    return Tr.tr.log(msg, dpth=4)


def log(msg='', *args, **kwargs):
    """ Use params args and kwargs to substitute {} in msg.
        Output msg to current/new Tr. 
        Simple usage:  
                log('a={}', 1)
            output
                [12.34"]fn:123 a=1
            where 
                [12.34"]    Time from start of logging
                fn          Name of unit where log was called
                123         Line number  where log was called
        More:
            log('###')  # Output stack info
            log('¬¶')   # Output chr(9) and chr(10) characters
    """
    if args or kwargs:
        msg = msg.format(*args, **kwargs)
    if Tr.tr is None:
        Tr.tr=Tr()
    return Tr.tr.log(msg)
    
class Tr :
    """ Logger.
        Usage:
            t = Tr()        # log as print
            t = Tr(path)    # log to the file
            t.log(sdata)    # output the sdata.
        """
    to_file=None
    tr=None

    sec_digs        = 2                                         # Digits in mantissa of second 
    se_fmt          = ''
    mise_fmt        = ''
    homise_fmt      = ''
    def __init__(self, log_to_file=None):
        log_to_file = log_to_file if log_to_file else Tr.to_file
        # Fields
        self.tm     = perf_counter()                            # Start tick for whole log

        if log_to_file:
            logging.basicConfig( filename=log_to_file
                                ,filemode='w'
                                ,level=logging.DEBUG
                                ,format='%(message)s'
                                ,datefmt='%H:%M:%S'
                                ,style='%')
        else: # to stdout
            logging.basicConfig( stream=sys.stdout
                                ,level=logging.DEBUG
                                ,format='%(message)s'
                                ,datefmt='%H:%M:%S'
                                ,style='%')
    def log(self, msg='', dpth=3) :
        logging.debug( self.format_msg(msg) )
        return self 
        # Tr.log
            
    def format_msg(self, msg, dpth=3, ops='+fun:ln'):
        if '###' in msg :
            # Output stack
            st_inf  = '\n###'
            for fr in inspect.stack()[dpth:]:
                try:
                    cls = fr[0].f_locals['self'].__class__.__name__ + '.'
                except:
                    cls = ''
                fun     = (cls + fr[3]).replace('.__init__','()')
                ln      = fr[2]
                st_inf  += '    {}:{}'.format(fun, ln)
            msg    += st_inf

        if '+fun:ln' in ops :
            frCaller= inspect.stack()[dpth]                     # 0-format_msg, 1-Tr.log, 2-log, 3-need func
            try:
                cls = frCaller[0].f_locals['self'].__class__.__name__ + '.'
            except:
                cls = ''
            fun     = (cls + frCaller[3]).replace('.__init__','()')
            ln      = frCaller[2]
            msg     = '[{}]{}:{} '.format( Tr.format_tm( perf_counter() - self.tm ), fun, ln ) + msg
        else : 
            msg     = '[{}] '.format( Tr.format_tm( perf_counter() - self.tm ) ) + msg

        return msg.replace('¬',C9).replace('¶',C10)
        # Tr.format

    @staticmethod
    def format_tm(secs) :
        """ Convert secs to 12h34'56.78" """
        if 0==len(Tr.se_fmt) :
            Tr.se_fmt       = '{:'+str(3+Tr.sec_digs)+'.'+str(Tr.sec_digs)+'f}"'
            Tr.mise_fmt     = "{:2d}'"+Tr.se_fmt
            Tr.homise_fmt   = "{:2d}h"+Tr.mise_fmt
        h = int( secs / 3600 )
        secs = secs % 3600
        m = int( secs / 60 )
        s = secs % 60
        return Tr.se_fmt.format(s) \
                if 0==h+m else \
               Tr.mise_fmt.format(m,s) \
                if 0==h else \
               Tr.homise_fmt.format(h,m,s)
        # Tr.format_tm
    # Tr

#########################
#NOTE: misc for OS 
#########################

def get_translation(plug_file):
    ''' Part of i18n.
        Full i18n-cycle:
        1. All GUI-string in code are used in form 
            _('')
        2. These string are extracted from code to 
            lang/messages.pot
           with run
            python.exe <pypython-root>\Tools\i18n\pygettext.py -p lang <plugin>.py
        3. Poedit (or same program) create 
            <module>\lang\ru_RU\LC_MESSAGES\<module>.po
           from (cmd "Update from POT") 
            lang/messages.pot
           It allows to translate all "strings"
           It creates (cmd "Save")
            <module>\lang\ru_RU\LC_MESSAGES\<module>.mo
        4. <module>.mo can be placed also in dir 
            CudaText\data\langpy\ru_RU\LC_MESSAGES\<module>.mo
           The dir is used first.
        5. get_translation uses the file to realize
            _('')
    '''
    lng     = app.app_proc(app.PROC_GET_LANG, '')
    plug_dir= os.path.dirname(plug_file)
    plug_mod= os.path.basename(plug_dir)
    lng_dirs= [ 
                app.app_path(app.APP_DIR_DATA)  +os.sep+'langpy',
                plug_dir                        +os.sep+'lang', 
              ]
    _       =  lambda x: x
    pass;                      #return _
    for lng_dir in lng_dirs:
        lng_mo  = lng_dir+'/{}/LC_MESSAGES/{}.mo'.format(lng, plug_mod)
        if os.path.isfile(lng_mo):
            t   = gettext.translation(plug_mod, lng_dir, languages=[lng])
            _   = t.gettext
            t.install()
            break
    return _
   #def get_translation

#_   = get_translation(__file__) # I18N

def get_desktop_environment():
    #From http://stackoverflow.com/questions/2035657/what-is-my-current-desktop-environment
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=652320
    # and http://ubuntuforums.org/showthread.php?t=1139057
    if sys.platform in ["win32", "cygwin"]:
        return "win"
    elif sys.platform == "darwin":
        return "mac"
    else: #Most likely either a POSIX system or something not much common
        def is_running(process):
            #From http://www.bloggerpolis.com/2011/05/how-to-check-if-a-process-is-running-using-python/
            # and http://richarddingwall.name/2009/06/18/windows-equivalents-of-ps-and-kill-commands/
            try: #Linux/Unix
                s = subprocess.Popen(["ps", "axw"],stdout=subprocess.PIPE)
            except: #Windows
                s = subprocess.Popen(["tasklist", "/v"],stdout=subprocess.PIPE)
            for x in s.stdout:
                if re.search(process, str(x)):
                    return True
            return False

        desktop_session = os.environ.get("DESKTOP_SESSION")
        if desktop_session is not None: #easier to match if we doesn't have  to deal with caracter cases
            desktop_session = desktop_session.lower()
            if desktop_session in ["gnome","unity", "cinnamon", "mate", "xfce4", "lxde", "fluxbox", 
                                   "blackbox", "openbox", "icewm", "jwm", "afterstep","trinity", "kde"]:
                return desktop_session
            ## Special cases ##
            # Canonical sets $DESKTOP_SESSION to Lubuntu rather than LXDE if using LXDE.
            # There is no guarantee that they will not do the same with the other desktop environments.
            elif "xfce" in desktop_session or desktop_session.startswith("xubuntu"):
                return "xfce4"
            elif desktop_session.startswith("ubuntu"):
                return "unity"       
            elif desktop_session.startswith("lubuntu"):
                return "lxde" 
            elif desktop_session.startswith("kubuntu"): 
                return "kde" 
            elif desktop_session.startswith("razor"): # e.g. razorkwin
                return "razor-qt"
            elif desktop_session.startswith("wmaker"): # e.g. wmaker-common
                return "windowmaker"
        if os.environ.get('KDE_FULL_SESSION') == 'true':
            return "kde"
        elif os.environ.get('GNOME_DESKTOP_SESSION_ID'):
            if not "deprecated" in os.environ.get('GNOME_DESKTOP_SESSION_ID'):
                return "gnome2"
        #From http://ubuntuforums.org/showthread.php?t=652320
        elif is_running("xfce-mcs-manage"):
            return "xfce4"
        elif is_running("ksmserver"):
            return "kde"
    return "unknown"


#########################
#NOTE: CudaText helpers
#########################
def ed_of_file_open(op_file):
    if not app.file_open(op_file):
        return None
    for h in app.ed_handles(): 
        op_ed   = app.Editor(h)
        if op_ed.get_filename() and os.path.samefile(op_file, op_ed.get_filename()):
            return op_ed
    return None
   #def ed_of_file_open

def get_hotkeys_desc(cmd_id, ext_id=None, keys_js=None, def_ans=''):
    """ Read one or two hotkeys for command 
            cmd_id [+ext_id]
        from 
            settings\keys.json
        Return 
            def_ans                     If no  hotkeys for the command
            'Ctrl+Q'            
            'Ctrl+Q * Ctrl+W'           If one hotkey  for the command
            'Ctrl+Q/Ctrl+T'            
            'Ctrl+Q * Ctrl+W/Ctrl+T'    If two hotkeys for the command
    """
    if keys_js is None:
        keys_json   = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'keys.json'
        keys_js     = apx._json_loads(open(keys_json).read()) if os.path.exists(keys_json) else {}

    cmd_id  = f('{},{}', cmd_id, ext_id) if ext_id else cmd_id
    if cmd_id not in keys_js:
        return def_ans
    cmd_keys= keys_js[cmd_id]
    desc    = '/'.join([' * '.join(cmd_keys.get('s1', []))
                       ,' * '.join(cmd_keys.get('s2', []))
                       ]).strip('/')
    return desc
   #def get_hotkeys_desc

@lru_cache(maxsize=32)
def get_plugcmd_hotkeys(plugcmd):
    lcmds   = app.app_proc(app.PROC_GET_COMMANDS, '')
    cfg_keys= [(cmd['key1'], cmd['key2'])
                for cmd in lcmds 
                if cmd['type']=='plugin' and cmd['p_method']==plugcmd][0]
    return cfg_keys
   #def get_plugcmd_hotkeys


######################################
#NOTE: plugins history
######################################
PLING_HISTORY_JSON  = app.app_path(app.APP_DIR_SETTINGS)+os.sep+'plugin history.json'
def get_hist(key_or_path, default=None, module_name='_auto_detect', to_file=PLING_HISTORY_JSON):
    """ Read from "plugin history.json" one value by string key or path (list of keys).
        Parameters
            key_or_path     Key(s) to navigate in json tree
                            Type: str or [str]
            default         Value to return if no suitable node in json tree
            module_name     Start node to navigate.
                            If it is '_auto_detect' then name of caller module is used.
                            If it is None then it is skipped (see examples).
            to_file         Name of file to read. APP_DIR_SETTING will be joined if no full path.
        
        Return              Found value or default
            
        Examples (caller module is 'plg')
        1. If no "plugin history.json"
                get_hist('k')                   returns None
                get_hist(['p', 'k'], 0)         returns 0
        2. If "plugin history.json" contains 
                {"k":1, "plg":{"k":2, "p":{"m":3}, "t":[0,1]}, "q":{"n":4}}
                get_hist('k', 0, None)          returns 1
                get_hist('k', 0)                returns 2
                get_hist('k', 0, 'plg')         returns 2
                get_hist('k', 0, 'oth')         returns 0
                get_hist(['p','m'], 0)          returns 3
                get_hist(['t'], [])             returns [0,1]
                get_hist('q', 0, None)          returns {'n':4}
                get_hist(['q','n'], 0, None)    returns 4
    """
    pass;                       log4fun=0                       # Order log in the function
    pass;                       log('key,def,mod,to_f={}',(key_or_path,default,module_name,to_file)) if iflog(log4fun,_log4mod) else 0
    to_file = to_file   if os.sep in to_file else   app.app_path(app.APP_DIR_SETTINGS)+os.sep+to_file
    if not os.path.exists(to_file):
        pass;                  #log('not exists',())
        return default
    data    = None
    try:
        data    = json.loads(open(to_file).read())
    except:
        pass;                   log('not load: {}',sys.exc_info())
        return default
    if module_name=='_auto_detect':
        caller_globals  = inspect.stack()[1].frame.f_globals
        module_name = inspect.getmodulename(caller_globals['__file__']) \
                        if '__file__' in caller_globals else None
    keys    = [key_or_path] if type(key_or_path)==str   else key_or_path
    keys    = keys          if module_name is None      else [module_name]+keys
    parents,\
    key     = keys[:-1], keys[-1]
    for parent in parents:
        data= data.get(parent)
        if type(data)!=dict:
            pass;              #log('not dict parent={}',(parent))
            return default
    return data.get(key, default)
   #def get_hist

def set_hist(key_or_path, value=None, module_name='_auto_detect', kill=False, to_file=PLING_HISTORY_JSON):
    """ Write to "plugin history.json" one value by key or path (list of keys).
        If any of node doesnot exist it will be added.
        Or remove (if kill) one key+value pair (if suitable key exists).
        Parameters
            key_or_path     Key(s) to navigate in json tree
                            Type: str or [str]
            value           Value to set if suitable item in json tree exists
            module_name     Start node to navigate.
                            If it is '_auto_detect' then name of caller module is used.
                            If it is None then it is skipped.
            kill            Need to remove node in tree.
                            if kill==True parm value is ignored
            to_file         Name of file to write. APP_DIR_SETTING will be joined if no full path.
        
        Return              value (param)   if !kill and modification is successful
                            value (killed)  if  kill and modification is successful
                            None            if  kill and no path in tree (no changes)
                            KeyError        if !kill and path has problem
            
        Examples (caller module is 'plg')
        1. If no "plugin history.json"  it will become
            set_hist('k',0,None)        {"k":0}
            set_hist('k',1)             {"plg":{"k":1}}
            set_hist('k',1,'plg')       {"plg":{"k":1}}
            set_hist('k',1,'oth')       {"oth":{"k":1}}
            set_hist('k',[1,2])         {"plg":{"k":[1,2]}}
            set_hist(['p','k'], 1)      {"plg":{"p":{"k":1}}}
        
        2. If "plugin history.json" contains    {"plg":{"k":1, "p":{"m":2}}}
                                                it will contain
            set_hist('k',0,None)                {"plg":{"k":1, "p":{"m":2}},"k":0}
            set_hist('k',0)                     {"plg":{"k":0, "p":{"m":2}}}
            set_hist('k',0,'plg')               {"plg":{"k":0, "p":{"m":2}}}
            set_hist('n',3)                     {"plg":{"k":1, "p":{"m":2}, "n":3}}
            set_hist(['p','m'], 4)              {"plg":{"k":1, "p":{"m":4}}}
            set_hist('p',{'m':4})               {"plg":{"k":1, "p":{"m":4}}}
            set_hist(['p','m','k'], 1)          KeyError (old m is not branch node)

        3. If "plugin history.json" contains    {"plg":{"k":1, "p":{"m":2}}}
                                                it will contain
            set_hist('k',       kill=True)      {"plg":{       "p":{"m":2}}}
            set_hist('p',       kill=True)      {"plg":{"k":1}}
            set_hist(['p','m'], kill=True)      {"plg":{"k":1, "p":{}}}
            set_hist('n',       kill=True)      {"plg":{"k":1, "p":{"m":2}}}    (nothing to kill)
    """
    pass;                       log4fun=0                       # Order log in the function
    pass;                      #log('key,val,mod,kill,to_f={}',(key_or_path, value, module_name, kill, to_file)) if iflog(log4fun,_log4mod) else 0
    to_file = to_file   if os.sep in to_file else   app.app_path(app.APP_DIR_SETTINGS)+os.sep+to_file
    body    = json.loads(open(to_file).read(), object_pairs_hook=odict) \
                if os.path.exists(to_file) and os.path.getsize(to_file) != 0 else \
              odict()

    if module_name=='_auto_detect':
        caller_globals  = inspect.stack()[1].frame.f_globals
        module_name = inspect.getmodulename(caller_globals['__file__']) \
                        if '__file__' in caller_globals else None
    pass;                      #log('to_file,module_name={}',(to_file,module_name))
    keys    = [key_or_path] if type(key_or_path)==str   else key_or_path
    keys    = keys          if module_name is None      else [module_name]+keys
    parents,\
    key     = keys[:-1], keys[-1]
    pass;                      #log('key,keys={}',(key,keys))
    data    = body
    for parent in parents:
        if kill and parent not in data:
            return None
        data= data.setdefault(parent, odict())
        if type(data)!=odict:
            raise KeyError()
    if kill:
        if key not in data:
            return None
        value       = data.pop(key)
    else:
        data[key]   =  value
    open(to_file, 'w').write(json.dumps(body, indent=2))
    return value
   #def set_hist

class Command:
    def execCurrentFileAsPlugin(self):
        fn  = ed.get_filename()
        if not fn.endswith('.py'):
            return app.msg_status(_('Fail. Use only for python file.'))
        ed.save()
        app.app_log(app.LOG_CONSOLE_CLEAR, 'm')
        cmd = f(r'exec(open(r"{}", encoding="UTF-8").read().lstrip("\uFEFF"))', fn)
        pass;                  #log('cmd={!r}',(cmd))
        ans     = app.app_proc(app.PROC_EXEC_PYTHON, cmd)
        print('>>> run {!r}'.format(fn))
        print(ans)
       #def execCurrentFileAsPlugin
   #class Command:

######################################
#NOTE: misc for CudaText
######################################

RE_CONST_NAME   = re.compile(r'(\w+)\s*=')
_const_name_vals= {}                        # {module:{name:val}}
def get_const_name(val, prefix='', module=app):
    """ Name of constant from the module starts with the prefix and has the value.
        If more then one names are found then return is concatination (with ",").
        Else return 'no_constant_starts_with_'+prefix+'_and_value_'+val.
    """
    mod_consts  = _const_name_vals.setdefault(module, {})
    if not mod_consts:
        with open(module.__file__) as f:
            for line in f:
                mtName = RE_CONST_NAME.match(line)
                if mtName:
                    nm  = mtName.group(1)
                    mod_consts[nm]  = getattr(module, nm)
    nms = [nm   for nm, vl in mod_consts.items()
                if  nm.startswith(prefix) and vl==val]
    return ','.join(nms) \
                if nms else \
           'no_constant_starts_with_'+prefix+'_and_value_'+str(val)
   #def get_app_const_name

######################################
#NOTE: misc for Python
######################################
def rgb_to_int(r,g,b):
    return r | (g<<8) | (b<<16)

def set_all_for_tree(tree, sub_key, key, val):
    for node in tree:
        if sub_key in node:
            set_all_for_tree(node[sub_key], sub_key, key, val)
        else:
            node[key]   = val
    return tree
   #def set_all_for_tree

def upd_dict(d1, d2):
    rsp = d1.copy()
    rsp.update(d2)
    return rsp
   #def upd_dict

def deep_upd(dcts):
    pass;                      #log('dcts={}',(dcts))
    if not dcts:
        return dcts
    if isinstance(dcts, dict):
        return dcts

    dct1, *dcts = dcts
    pass;                      #log('dct1, dcts={}',(dct1, dcts))
    rsp   = dct1.copy()
    for dct in dcts:
        for k,v in dct.items():
            if False:pass
            elif k not in rsp:
                rsp[k]  = v
            elif isinstance(rsp[k], dict) and isinstance(v, dict):
                rsp[k].update(v)
            else:
                rsp[k]  = v
    pass;                      #log('rsp={}',(rsp))
    return rsp
   #def deep_upd

def dispose(dct, key):
    " Remove the key from the dict (if is) and return the dict. "
    if key in dct:
        del dct[key]
    return dct
   #def dispose

def likesint(what):     return isinstance(what, int)
def likesstr(what):     return isinstance(what, str)
def likeslist(what):    return isinstance(what, tuple) or isinstance(what, list)
   
if __name__ == '__main__' :
    # To start the tests run in Console
    #   exec(open(path_to_the_file, encoding="UTF-8").read())

    app.app_log(app.LOG_CONSOLE_CLEAR, 'm')
    print('Start all tests')
    if -1==-1:
        print('Start tests: log')
        log('n={}',1.23)
        log('n,s¬=¶{}',(1.23, 'abc'))
        def my():
            log('a={}',1.23)
            def sub():
                log('###')
            class CMy:
                def meth(self):
                    log('###')
            sub()
            CMy().meth()
        my()
        print('Stop tests: log')

    if -2==-2:
        print('Start tests: plugin history')

        for smk in [smk for smk 
            in  sys.modules                             if 'cuda_kv_base.tests.test_hist' in smk]:
            del sys.modules[smk]        # Avoid old module 
        import                                              cuda_kv_base.tests.test_hist
        import unittest
        suite = unittest.TestLoader().loadTestsFromModule(  cuda_kv_base.tests.test_hist)
        unittest.TextTestRunner().run(suite)
        
        print('Stop tests: plugin history')
    print('Stop all tests')
'''
ToDo
[+][kv-kv][11feb19] Extract from cd_plug_lib.py
[+][kv-kv][11feb19] Set tests
[ ][kv-kv][24mar19] Rename upd_dict
'''
