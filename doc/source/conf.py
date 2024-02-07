import pathlib
import os
import re
import shlex
import subprocess
from _simple_build_system._sphinxutils import _get_gitversion

 # Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'simplebuild-dgcode'
copyright = '2013-2024, ESS ERIC and simplebuild developers'
author = 'Thomas Kittelmann'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

nitpicky = True
extensions = [
    # 'myst_parser', #for parsing .md files?
    'sphinxarg.ext',
    'sphinx_toolbox.sidebar_links',
    'sphinx_toolbox.github',
    'sphinx_toolbox.collapse',
    #'sphinx_licenseinfo',

    #Issue roles (pip install sphinx-issues,
    #             docs at https://github.com/sloria/sphinx-issues):
    #'sphinx_issues',
    ]


#Fix env:
os.environ['PYTHONUNBUFFERED'] = '1'
if 'SIMPLEBUILD_CFG' in os.environ:
    del os.environ['SIMPLEBUILD_CFG']

def _reporoot():
    p=pathlib.Path(__file__).parent.parent.parent
    assert ( p / 'src' / 'simplebuild_dgcode'/ '__init__.py' ).is_file()
    return p.absolute()

version = _get_gitversion( _reporoot() )

# for :sbpkg:`MyPkg` links
extensions += '_simple_build_system._sphinxext',
def _sbbundles():
    sbdgversion='main'
    if re.match(r"^v[0-9]+\.[0-9]+\.[0-9]+$", version ):
        sbdgversion = version
    sbversion='main' # probably is best to keep at main
    sbdgdata = _reporoot() / 'src' / 'simplebuild_dgcode' / 'data'
    import _simple_build_system as _
    sbdata = pathlib.Path(_.__file__).parent / 'data'
    sbdgdata_online = f'https://github.com/mctools/simplebuild-dgcode/[blob|tree]/{sbdgversion}/src/simplebuild_dgcode/data'
    sbdata_online = f'https://github.com/mctools/simplebuild/[blob|tree]/{sbversion}/src/_simple_build_system/data'

    bundles = { 'dgcode' : ( sbdgdata / 'pkgs', sbdgdata_online + '/pkgs' ),
                'dgcode_val' : ( sbdgdata / 'pkgs_val', sbdgdata_online + '/pkgs_val' ),
                'core' :  ( sbdata / 'pkgs-core', sbdata_online + '/pkgs-core' ),
                'core_val' : ( sbdata / 'pkgs-core_val', sbdata_online + '/pkgs-core_val' ),
               }
    return bundles
simplebuild_pkgbundles = _sbbundles()

def setup(app):
    #Avoid horizontal scroll-bars in tables (see
    #https://stackoverflow.com/a/40650120):
    app.add_css_file('custom.css')

#https://img.shields.io/github/issues/mctools/simplebuild
#https://img.shields.io/github/issues/mctools/simplebuild/bug
#https://img.shields.io/github/issues/detail/state/mctools/simplebuild/36
#https://img.shields.io/github/issues/detail/state/mctools/simplebuild/41

#For the toolbox.sidebar_links:
github_username = 'mctools'
github_repository = 'simplebuild-dgcode'

#For the 'sphinx_issues' extension:
issues_default_group_project = f"{github_username}/{github_repository}"

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output #noqa E501

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
#html_logo = 'icon/favicon-32x32.png'
html_favicon = 'icon/favicon-32x32.png'
#html_sidebars = { '**': ['globaltoc.html', 'searchbox.html'] }

github_url = 'https://github.com/mctools/simplebuild-dgcode'

html_theme_options = {
    'logo_only': False,
    'collapse_navigation' : False,
    'sticky_navigation': True, #sidebar stays in place while contents scrolls
    'navigation_with_keys': True, #navigate with left/right arrow keys
    'navigation_depth': 4,
}
#html_theme_options = {
#    'logo': 'icon/android-chrome-192x192.png',
#    # etc.
#}
#

#html_sidebars = { '**': ['globaltoc.html', 'relations.html',
#                         'sourcelink.html', 'searchbox.html'] }

#html_theme_options = {
#    ...
#    "home_page_in_toc": True
#    ...
#}
#

###############################################################################

def prepare_tricorderproj_dir():
    confpydir = pathlib.Path(__file__).parent
    blddir = confpydir.parent / 'build'
    blddir.mkdir(exist_ok=True)
    assert blddir.exists()
    root = blddir / 'autogen_tricorder_projdir'
    already_done = root.is_dir()
    if not already_done:
        root.mkdir()
    class dirs:
        pass
    d = dirs()
    d.root = root
    d.blddir = blddir
    d.confpydir = confpydir
    d.already_done = already_done
    return d

def invoke( *args, **kwargs ):
    assert len(args)>0
    cmd = args[0]
    cmdstr = shlex.join( cmd )
    orig_check = kwargs.get('check')
    if 'check' in kwargs:
        del kwargs['check']
    cwd = kwargs.get('cwd')
    assert cwd
    orig_capture_output = kwargs.get('capture_output')
    kwargs['capture_output'] = True
    p = subprocess.run( *args, **kwargs )
    if orig_check:
        if p.returncode != 0 or p.stderr:
            print(p.stderr.decode())
            print(p.stdout.decode())
            raise RuntimeError(f'Command in dir {cwd} failed!: {cmdstr}')
    if p.stderr and (orig_check or orig_capture_output ):
            print(p.stderr.decode())
            print(p.stdout.decode())
            raise RuntimeError(f'Command in dir {cwd} had stderr output!: {cmdstr}')
    return p

def invoke_in_pkgroot( cmd, pkgroot, outfile ):
    cmdstr = ' '.join( shlex.quote(e) for e in cmd )
    print(f' ---> Launching command {cmdstr}')
    if cmd[0].startswith('sb_'):
        cmd = ['sbenv']+cmd
    p = invoke( cmd,
                cwd = pkgroot,
                check = True )
    assert not p.stderr
    txt = p.stdout.decode()
    from _simple_build_system._sphinxutils import fixuptext
    txt = fixuptext( pkgroot, p.stdout.decode() )
    txt = f'$> {cmdstr}\n' + txt
    outfile.write_text(txt)

def read_text_remove_comments( fpath, cmtchar = '#' ):
    out = []
    for line in fpath.read_text().splitlines():
        if line.strip().startswith(cmtchar):
            continue
        if ( not line.strip()
             and out
             and not out[-1] ):
            continue#no duplicate empty lines
        out.append( line.rstrip() )
    while out and not out[0]:
        out = out[1:]
    while out and not out[-1]:
        out = out[:-1]
    if not out:
        return '\n'
    if out[-1]:
        out.append('')
    return '\n'.join(out)

def run_tricorder_cmds():
    tricorder_dirs = prepare_tricorderproj_dir()
    pkgroot = tricorder_dirs.root
    bd = tricorder_dirs.blddir
    c0 = bd / 'autogen_tricorder_sbinit.txt'
    c1 = bd / 'autogen_tricorder_newsimproj_sb0.txt'
    if tricorder_dirs.already_done:
        print(">> Skipping tricorder_cmds (already ran).")
    else:
        invoke_in_pkgroot( ['sb','--init','dgcode'],
                           pkgroot,
                           c0 )
        invoke_in_pkgroot( ['sb'],
                           pkgroot,
                           c1 )
        invoke_in_pkgroot( ['dgcode_newsimproject','-h'],
                           pkgroot,
                           bd / 'autogen_tricorder_newsimproj_help.txt' )
        invoke_in_pkgroot( ['dgcode_newsimproject','TriCorder'],
                           pkgroot,
                           bd / 'autogen_tricorder_newsimproj_TriCorder.txt' )
        invoke_in_pkgroot( ['sb','--tests'],
                           pkgroot,
                           bd / 'autogen_tricorder_newsimproj_sbtests.txt' )
        invoke_in_pkgroot( ['sb_g4xsectdump_query','-h'],
                           pkgroot,
                           bd / 'autogen_tricorder_g4xsectdump_query_help.txt' )
        invoke_in_pkgroot( ['sb_xsectparse_plotfile','-h'],
                           pkgroot,
                           bd / 'autogen_tricorder_xsectparse_plotfile_help.txt' )
        invoke_in_pkgroot( ['sb_tricorder_sim','-h'],
                           pkgroot,
                           bd / 'autogen_tricorder_sim_help.txt' )
        invoke_in_pkgroot( ['sb_tricorder_sim','-p'],
                           pkgroot,
                           bd / 'autogen_tricorder_sim_p.txt' )
        invoke_in_pkgroot( ['sb_tricorder_sim','-g'],
                           pkgroot,
                           bd / 'autogen_tricorder_sim_g.txt' )
        invoke_in_pkgroot( ['sb_g4utils_querygenerator',
                            '-g','G4StdGenerators.SimpleGen'],
                           pkgroot,
                           bd / 'autogen_querygenerator_simplegen.txt' )
        invoke_in_pkgroot( ['sb_g4utils_querygenerator',
                            '-g','G4StdGenerators.FlexGen'],
                           pkgroot,
                           bd / 'autogen_querygenerator_flexgen.txt' )
        invoke_in_pkgroot( ['sb_g4utils_querygenerator',
                            '-g','G4StdGenerators.ProfiledBeamGen'],
                           pkgroot,
                           bd / 'autogen_querygenerator_profiledbeamgen.txt' )
        invoke_in_pkgroot( ['sb_tricorder_sim'],
                           pkgroot,
                           bd / 'autogen_tricorder_sim_noargs.txt' )
        invoke_in_pkgroot( ['sb_tricorder_sim','--heatmap=help'],
                           pkgroot,
                           bd / 'autogen_tricorder_simheatmaphelp.txt' )
        invoke_in_pkgroot( ['sb_tricorder_sim','--mcpl=help'],
                           pkgroot,
                           bd / 'autogen_tricorder_simmcplhelp.txt' )
        invoke_in_pkgroot( ['nctool','-d','stdlib::Al_sg225.ncmat;temp=250K'],
                           pkgroot,
                           bd / 'autogen_nctool_dump_example.txt' )
        invoke_in_pkgroot( ['sb_g4materials_dump',
                            'G4_STAINLESS-STEEL:temp_kelvin=200:scale_density=1.1'],
                           pkgroot,
                           bd / 'autogen_g4matdump_g4stainlesssteel.txt' )

    tc_simscript = pkgroot/'TriCorder'/'TriCorder'/'scripts'/'sim'
    tc_simscript_txt = read_text_remove_comments( tc_simscript )
    assert 'launcher.go()' in tc_simscript_txt
    assert 'launcher.setOutput' in tc_simscript_txt
    assert 'geo=' in tc_simscript_txt.replace(' ','')
    assert 'gen=' in tc_simscript_txt.replace(' ','')
    assert 'G4Launcher(geo,gen)' in tc_simscript_txt.replace(' ','')
    ( bd / 'autogen_tricorder_simscript_wocomments.py'
     ).write_text( tc_simscript_txt )


    tc_geomod = ( pkgroot/'TriCorder'/'G4GeoTriCorder'/
                  'pycpp_GeoTriCorder'/'geometry_module.cc')
    tc_geomod_txt = read_text_remove_comments( tc_geomod, '//' )
    for e in ('getParameterMaterial','getMaterial','place',
              '"material_lab"','"material_sample"',
              '"sample_posz_mm"','Units::mm'):
        assert e in tc_geomod_txt
    #assert 'launcher.go()' in tc_geomod_txt
    #assert 'launcher.setOutput' in tc_geomod_txt
    #assert 'geo=' in tc_geomod_txt.replace(' ','')
    #assert 'gen=' in tc_geomod_txt.replace(' ','')
    #assert 'G4Launcher(geo,gen)' in tc_geomod_txt.replace(' ','')
    ( bd / 'autogen_tricorder_geomod_wocomments.cc'
     ).write_text( tc_geomod_txt )

    for n in ('scan','scanana'):
        orig = pkgroot/'TriCorder'/'TriCorder'/'scripts'/n
        wocomments = read_text_remove_comments( orig )
        ( bd / f'autogen_tricorder_script_{n}' ).write_text( wocomments )
        #In the usage in the docs, we assume the script does not contain the
        #name of the project:
        #assert not 'tricorder' in wocomments.lower()
        if n == 'scan':
            assert 'plot1' in wocomments
            assert 'plot2' in wocomments
#Snip between:
#G4Launcher:: Calling G4RunManager::Initialize()
#G4Launcher:: Begin simulation of event 1 [seed 123456789]

    edit = c0.read_text()
    ll = c1.read_text().splitlines()
    while ll[0].startswith('$>'):
        edit += ll[0]+'\n'
        ll = ll[1:]
    ntop,nbottom=5,5
    for i,line in enumerate(ll):
        if i < ntop or i >= len(ll)-nbottom:
            edit += line.rstrip()+'\n'
        elif i==ntop:
            nstripped = len(ll)-ntop-nbottom
            edit += ( f'<<\n<< {nstripped} LINES OF ACTUAL BUILD OUTPUT'
                      ' NOT SHOWN HERE >>\n<<\n' )
    (c0.parent
     /c0.name.replace('.txt','_plus_snippet_sb.txt')).write_text(edit)

run_tricorder_cmds()
