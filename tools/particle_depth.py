"""CSS-only view-space depth shading shared by the two particle artworks."""

def coefficients(rotations, scaled=False):
    def mul(a,b):
        if a=='0' or b=='0':return '0'
        if a=='1':return b
        if b=='1':return a
        return f'(({a}) * ({b}))'
    row=['0','0','1']
    for axis,angle in reversed(rotations):
        c=f'cos({angle})';s=f'sin({angle})';neg=f'(-1 * {s})'
        m={'x':[['1','0','0'],['0',c,neg],['0',s,c]],'y':[[c,'0',s],['0','1','0'],[neg,'0',c]],'z':[[c,neg,'0'],[s,c,'0'],['0','0','1']]}[axis]
        row=[' + '.join(t for t in [mul(row[k],m[k][j]) for k in range(3)] if t!='0') or '0' for j in range(3)]
    return ';'.join(f'--depth-{axis}:calc(({expr})' + (' * var(--bs)' if scaled and axis in 'xy' else '') + ')' for axis,expr in zip('xyz',row))

def depth_css(selector,parent,rotations):
    css=''
    for name,inherit,default in [('px','false',0),('py','false',0),('pz','false',0),('pulse','false',1),('dx','true',0),('dy','true',0),('dz','true',0),('cx','true',0),('cy','true',0),('bx','true',0),('bz','true',0),('bs','true',1)]:
        css+=f'@property --{name}{{syntax:"<number>";inherits:{inherit};initial-value:{default}}}'
    for axis in 'xyz':css+=f'@property --depth-{axis}{{syntax:"<number>";inherits:true;initial-value:{1 if axis=="z" else 0}}}'
    css+=parent+'{'+coefficients(rotations,parent=='.band')+'}'
    css+=selector+'''{--view-depth:calc(var(--depth-x)*var(--px) + var(--depth-y)*var(--py) + var(--depth-z)*var(--pz));--near:clamp(0,calc((var(--view-depth) + 230)/460),1);--depth-size:calc(.5 + var(--near)*1.25);transform:translate3d(calc(var(--px)*1px),calc(var(--py)*1px),calc(var(--pz)*1px)) scale(calc(var(--pulse)*var(--depth-size)))!important;opacity:calc(.16 + var(--near)*.84)!important}'''
    return css
