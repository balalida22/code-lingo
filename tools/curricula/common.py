from build import S,lesson

# Dialect-specific executable forms; no runtime translation in the app.
D={
'c': ('int x = {v};','x = {v};','printf("%d", {v});','printf("%s", {v});','int','"{w}"'),
'cpp':('int x = {v};','x = {v};','std::cout << {v};','std::cout << {v};','int','std::string("{w}")'),
'rust':('let mut x = {v};','x = {v};','println!("{{}}", {v});','println!("{{}}", {v});','i32','"{w}"'),
'ruby':('x = {v}','x = {v}','puts {v}','puts {v}','Integer','"{w}"'),
'lua':('local x = {v}','x = {v}','print({v})','print({v})','number','"{w}"'),
'php':('$x = {v};','$x = {v};','echo {v};','echo {v};','int','"{w}"'),
'perl':('my $x = {v};','$x = {v};','print({v});','print({v});','scalar','"{w}"'),
}
def basics(cid):
    decl,assign,out,sout,typ,lit=D[cid]; x='$x' if cid in ('php','perl') else 'x'
    def o(v):return out.format(v=v)
    def d(v):return decl.format(v=v)
    def a(v):return assign.format(v=v)
    def expr(v):return o('~'+v+'~')
    def st(w):return lit.format(w=w)
    div='int(${n} / ${m})' if cid=='perl' else '${n} // ${m}' if cid=='lua' else 'intdiv(${n}, ${m})' if cid=='php' else '${n} / ${m}'
    L=[lesson('values','Values and assignment','A variable names a value. Assignment updates that variable; an earlier copied number does not follow later assignments. Read statements from top to bottom.',
      S(d('~${n}~')+'\n'+o(x),'${n}','${next}|0','The declaration stores ${n}; the output reads that stored value.','${next}|0'),
      S(d('${n}')+'\n'+a('~${m}~')+'\n'+o(x),'${m}','${n}|${add}','The second assignment replaces the old value with ${m}.','${n}|${add}'),
      S(d('${n}')+'\n'+expr(x+' + ${m}'),'${add}','${mul}|${n}','Adding ${m} computes a new value without changing the variable.',x+' * ${m}|'+x),
      S(d('${n}')+'\n'+a(x+' + ~1~')+'\n'+o(x),'${next}','${n}|${prev}','Reading the old value and adding one updates the variable once.','0|2')),
      lesson('arithmetic','Arithmetic and precedence','Multiplication binds more tightly than addition. Parentheses group expressions. Integer quotient and remainder answer different questions; all operands here are positive.',
      S(expr('${n} + ${m} * 2'),'${n_plus_twom}','${doubleadd}|${mul}','Multiplication happens first, then ${n} is added.','(${n} + ${m}) * 2|${n} * ${m}'),
      S(expr('(${n} + ${m}) * 2'),'${doubleadd}','${n_plus_twom}|${add}','Parentheses force addition before doubling.','${n} + ${m} * 2|${n} + ${m}'),
      S(expr(div),'${div}','${rem}|${mul}','This expression computes the positive integer quotient, discarding the fractional part.','${n} % ${m}|${n} * ${m}'),
      S(expr('${n} % ${m}'),'${rem}','${mul}|${add}','Remainder is what remains after dividing into complete groups of ${m}.','${n} * ${m}|${n} + ${m}'))]
    # Add arithmetic derived expressions in the shared authoring registry.
    from build import DERIVED
    DERIVED.update(n_plus_twom='n+m*2',doubleadd='(n+m)*2')
    return L
