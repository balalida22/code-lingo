"""Native course assembly. Preserve legacy IDs; repairs get distinct IDs.

Python already has an idiomatic curriculum; Rust is assembled by rust_course.
No database writes or migration-by-renumbering take place here.
"""
from build import S, source

ORDERS={
 'c': ('build values integer-model arithmetic conditions loops',
       'strings arrays pointers functions records io buffers',
       'units storage memory errors bits callbacks cli'),
 'cpp': ('build values initialization arithmetic strings conditions loops',
         'functions containers names classes ownership value-semantics io',
         'exceptions templates views variants polymorphism concurrency'),
 'ruby': ('cli values arithmetic strings conditions loops',
          'methods keywords collections patterns io text errors',
          'objects modules blocks enumeration mutation protocols testing'),
 'lua': ('runtime values arithmetic strings conditions loops',
         'functions results tables iteration io scope patterns',
         'references metatables methods errors resources coroutines embedding'),
 'php': ('runtime values arithmetic strings conditions loops',
         'functions arrays io validation http json errors',
         'namespaces objects contracts modern-contracts closures generators database'),
 'perl': ('cli values arithmetic strings conditions loops',
          'subroutines collections context io text-pipeline regex regex-repairs',
          'modules errors references scope-state file-boundaries objects testing'),
 'typescript': ('tooling values expressions branches loops functions',
               'objects structural arrays validation modules errors classes',
               'generics keyed-types unions utilities contracts async async-boundaries'),
 'web': ('html semantics forms css layout grid javascript',
         'functions scope-values dom events event-loop data responsive',
         'forms-data async fetch modules browser-state integration'),
 'sql': ('select expressions null-logic filter order schema affinity',
         'writes aggregation joins join-boundaries subqueries views dates-sets',
         'transactions integrity windows window-frames safequeries schema-changes'),
}

REFERENCES={
 'c': [('c-standard','C17 committee draft N2176','https://www.open-std.org/jtc1/sc22/wg14/www/docs/n2176.pdf'),
       ('gcc','GCC: compilation stages and output options','https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html')],
 'cpp': [('cpp-guidelines','C++ Core Guidelines: values, interfaces, resources, concurrency','https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines')],
 'ruby': [('ruby-syntax','Ruby 3.3 syntax reference','https://docs.ruby-lang.org/en/3.3/syntax_rdoc.html'),
          ('ruby-patterns','Ruby pattern matching','https://docs.ruby-lang.org/en/3.3/syntax/pattern_matching_rdoc.html'),
          ('ruby-methods','Ruby method definitions and arguments','https://docs.ruby-lang.org/en/3.3/syntax/methods_rdoc.html')],
 'lua': [('lua-manual','Lua 5.4 reference manual: language, libraries, embedding','https://www.lua.org/manual/5.4/manual.html')],
 'php': [('php-manual','PHP manual: language and standard extensions','https://www.php.net/manual/en/'),
         ('php-pdo','PDO prepared statements','https://www.php.net/manual/en/pdo.prepared-statements.php')],
 'perl': [('perl-run','Perl invocation and one-liners','https://perldoc.perl.org/perlrun'),
          ('perl-regex','Perl regular expression tutorial','https://perldoc.perl.org/perlretut'),
          ('perl-sub','Perl subroutines and scope','https://perldoc.perl.org/perlsub'),
          ('perl-test','Core Test::More','https://perldoc.perl.org/Test::More')],
 'typescript': [('ts-types','TypeScript Handbook: everyday types','https://www.typescriptlang.org/docs/handbook/2/everyday-types.html'),
                ('ts-narrow','TypeScript Handbook: narrowing','https://www.typescriptlang.org/docs/handbook/2/narrowing.html'),
                ('ts-config','TSConfig reference','https://www.typescriptlang.org/tsconfig/'),
                ('ts-types-from-types','TypeScript Handbook: creating types from types','https://www.typescriptlang.org/docs/handbook/2/types-from-types.html')],
 'web': [('mdn-forms','MDN: sending form data','https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Sending_and_retrieving_form_data'),
         ('mdn-events','MDN: JavaScript execution model','https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Execution_model'),
         ('mdn-grid','MDN: CSS Grid layout','https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout')],
 'sql': [('sqlite-types','SQLite datatypes and affinity','https://www.sqlite.org/datatype3.html'),
         ('sqlite-select','SQLite SELECT processing','https://www.sqlite.org/lang_select.html'),
         ('sqlite-window','SQLite window functions','https://www.sqlite.org/windowfunctions.html'),
         ('sqlite-alter','SQLite ALTER TABLE','https://www.sqlite.org/lang_altertable.html'),
         ('sqlite-date','SQLite date and time functions','https://www.sqlite.org/lang_datefunc.html')],
}

def repairs(cid):
 """Keyed by stable read family, with a successful replacement scenario."""
 return {
 'c': {
 ('build',2): S('~int size(void){return ${n};}~\n/* in main */ printf("%d",size());','${n}','Link error|0','Provide a function definition with the declared signature so the call can be linked.','int size(void);|int other(void){return ${n};}'),
 ('arrays',3): S('int a[]={${n},${m}}; printf("%d",~a[1]~);','${m}','${n}|0','Use the valid second-element index of this two-element array.','a[2]|a[3]'),
 ('memory',1): S('int *p=malloc(sizeof *p); if(p) { *p=${n}; printf("%d",~*p~); free(p); }','${n}','0|An address','Read the live object before releasing its storage.','p|&p'),
 ('pointers',3): S('int good(void) { int x=${n}; return ~x~; }\n/* in main */ printf("%d",good());','${n}','0|An address','Return the integer value rather than a pointer to an expired local.','&x|NULL'),
 ('integer-model',3): S('int x=INT_MAX; if (~x < INT_MAX~) ++x; printf("%d",x==INT_MAX);','1','0|Undefined behavior','Check that a signed increment is in range before performing it.','x == INT_MAX|x > 0'),
 },
 'cpp': {
 ('containers',3): S('std::vector<int> a={${n}}; std::cout<<a.~at(0)~;','${n}','0|Throws','Use the valid index zero for this one-element vector.','at(1)|at(2)'),
 ('names',3): S('~int~ x=${n}; x=${m}; std::cout<<x;','${m}','${n}|Compile error','Use a mutable integer when reassignment is required.','const int|const auto'),
 ('exceptions',1): S('try {throw std::invalid_argument("${word}");} catch (~const std::invalid_argument& e~) {std::cout<<e.what();}','${word}','Exception escapes|Compile error','Catch the specific exception by const reference at the boundary.','const std::out_of_range& e|int e'),
 ('initialization',0): S('int n~{2}~; std::cout<<n;','2','Compile error|3','Use an integer initializer when the intended value is exactly two.','{2.5}|{3}'),
 ('value-semantics',0): S('auto a=std::make_unique<int>(${n}); auto b=~std::move(a)~; std::cout<<*b;','${n}','Compile error|0','Transfer exclusive ownership rather than attempting to copy it.','a|nullptr'),
 ('views',3): S('~std::string~ owner="${word}"; std::string_view view=owner; std::cout<<view;','${word}','Undefined behavior|Empty string','Keep an owning string alive while the view is used.','int|char'),
 ('variants',1): S('std::variant<int,std::string> value="${word}"; std::cout<<std::~get<std::string>~(value);','${word}','Throws|Compile error','Select the active string alternative.','get<int>|get<double>'),
 ('concurrency',3): S('~std::atomic<int>~ value{0}; {std::jthread a([&]{++value;}); std::jthread b([&]{++value;});} std::cout<<value.load();','2','1|Undefined behavior','Use an atomic counter and join both threads before reading its result.','int|volatile int'),
 },
 'ruby': {
 ('errors',2): S('begin\n raise ArgumentError,"${word}"\n~rescue ArgumentError => error~\n puts error.message\nend','${word}','Exception escapes|nil','Handle the argument error at a boundary that can report its message.','rescue NameError => error|rescue NoMethodError => error'),
 ('mutation',2): S('original=[${n}].freeze\neditable=original.~dup~\neditable << ${m}\nputs editable.length','2','FrozenError|1','Duplicate the frozen array before modifying the new outer array.','itself|freeze'),
 ('keywords',1): S('def copies(count:); count; end\nputs copies(~count: ${n}~)','${n}','ArgumentError|0','Supply the required keyword count.','${n}|other: ${n}'),
 ('patterns',3): S('value=[${n}]\nvalue => ~[first]~\nputs first','${n}','NoMatchingPatternError|nil','Match the actual one-element structure.','[first,second]|[]'),
 },
 'lua': {
 ('errors',2): S('local ok,message=~pcall~(function() assert(false,"${word}") end)\nprint(ok)','false','An error escapes|true','A protected boundary converts the assertion failure into a false status.','assert|type'),
 ('resources',3): S('local ~value~ = ${n}\nvalue=${m}\nprint(value)','${m}','Compile error|${n}','Declare an ordinary local when reassignment is part of the contract.','value <const>|value <close>'),
 },
 'php': {
 ('errors',2): S('try {throw new InvalidArgumentException("${word}");} catch (~InvalidArgumentException $e~) {echo $e->getMessage();}','${word}','Exception escapes|TypeError','Catch the argument error at a boundary that can handle it.','TypeError $e|ParseError $e'),
 ('modern-contracts',1): S('class Limit {public function __construct(public readonly int $value) {}} $x=new Limit(${n}); $x=~new Limit(${m})~; echo $x->value;','${m}','Error|${n}','Create a new value object rather than reassigning a readonly property.','${m}|null'),
 ('modern-contracts',3): S('declare(strict_types=1); function size(int $n):int{return $n;} echo size(~${n}~);','${n}','TypeError|0','Supply an actual integer at this strict call boundary.','"${n}"|true'),
 },
 'perl': {
 ('errors',3): S('eval { die "${word}\\n"; }; print(~$@ ? "failed" : "ok"~);','failed','ok|Exception escapes','eval catches the exception; inspect $@ immediately afterward.','"ok"|$@ ? "ok" : "failed"'),
 },
 'typescript': {
 ('values',2): S('~let~ x=${n}; x=${m}; console.log(x);','${m}','Type error|${n}','Use let when the binding must be reassigned.','const|readonly'),
 ('objects',2): S('interface Box {readonly size:number} const b:Box={size:${n}}; const updated:Box=~{...b,size:${m}}~; console.log(updated.size);','${m}','Type error|${n}','Construct an updated value without mutating the readonly field.','b|{size:"${m}"}'),
 ('utilities',2): S('type Box={size:number}; const b:Readonly<Box>={size:${n}}; const updated:Box=~{...b,size:${m}}~; console.log(updated.size);','${m}','Type error|${n}','Create a new object to satisfy the immutable update contract.','b|{size:"${m}"}'),
 ('structural',1): S('interface Named {name:string}\nconst item:Named={~name:"${word}"~}; console.log(item.name);','${word}','Type error|undefined','Remove the unintended excess property while keeping the required name.','name:"${word}",typo:1|size:${n}'),
 ('validation',1): S('const value:unknown="${word}"; if(~typeof value === "string"~) console.log(value.toUpperCase());','${upper}','Type error|${word}','Narrow the unknown value before calling a string method.','value !== null|Boolean(value)'),
 ('contracts',2): S('// strict + exactOptionalPropertyTypes\nconst value:{name?:string}=~{}~; console.log(value.name ?? "${word}");','${word}','Type error|undefined','Represent absence by omitting the property under this compiler flag.','{name:undefined}|{name:null}'),
 },
 'web': {
 ('scope-values',3): S('{ ~let count=${n};~ console.log(count); }','${n}','ReferenceError|undefined','Initialize the block binding before reading it.','const other=${n};|'),
 },
 'sql': {
 ('schema',0): S('CREATE TABLE item(size INTEGER NOT NULL); INSERT INTO item VALUES(~${n}~); SELECT size FROM item;','${n}','Constraint error|NULL','Supply a non-null value that satisfies the existing schema.','NULL|0'),
 ('schema',2): S('CREATE TABLE item(size INTEGER CHECK(size>0)); INSERT INTO item VALUES(~${n}~); SELECT size FROM item;','${n}','Constraint error|0','Insert a positive value instead of weakening the intended constraint.','0|-1'),
 ('integrity',0): S('CREATE TABLE item(id INTEGER UNIQUE); INSERT INTO item VALUES(${n}); INSERT INTO item VALUES(~${next}~); SELECT COUNT(*) FROM item;','2','Constraint error|1','Use a distinct key for the new row.','${n}|${n}+0'),
 ('integrity',1): S('PRAGMA foreign_keys=ON; CREATE TABLE parent(id INTEGER PRIMARY KEY); CREATE TABLE child(pid INTEGER REFERENCES parent(id)); ~INSERT INTO parent VALUES(${n});~ INSERT INTO child VALUES(${n}); SELECT COUNT(*) FROM child;','1','Constraint error|0','Create the referenced parent before inserting the child; keep enforcement enabled.','INSERT INTO parent VALUES(0);|'),
 },
 }[cid]

def upgrade(cid,sources,lessons):
 from build import DERIVED
 DERIVED.update(tail='word[1:]',unicodebytes='len(word)+2',unicodechars='len(word)+1')
 from native_systems import c,cpp
 from native_scripts import ruby,lua
 from native_server_text import php,perl
 from native_web import typescript,web
 from native_sql import sql
 additions=dict(c=c,cpp=cpp,ruby=ruby,lua=lua,php=php,perl=perl,typescript=typescript,web=web,sql=sql)[cid]()
 combined={l['id']:l for l in lessons+additions}
 for l in combined.values():
     l['scenarios']=list(l['scenarios'])
 refs=REFERENCES[cid]
 sources=sources+[source(*entry) for entry in refs]
 default_ref=refs[0][0]
 for l in additions:
     l['sources']=[default_ref]
 # More precise provenance for the native topic boundaries.
 specific={
  'c': {'build':['gcc']},
  'ruby': {'patterns':['ruby-patterns'],'keywords':['ruby-methods']},
  'php': {'database':['php-pdo']},
  'perl': {'regex-repairs':['perl-regex'],'scope-state':['perl-sub'],'testing':['perl-test']},
  'typescript': {'tooling':['ts-config'],'contracts':['ts-config','ts-types-from-types'],'validation':['ts-narrow'],'keyed-types':['ts-types-from-types']},
  'web': {'semantics':['mdn'],'grid':['mdn-grid'],'scope-values':['js'],'event-loop':['mdn-events'],'forms-data':['mdn-forms'],'browser-state':['mdn','js']},
  'sql': {'null-logic':['sqlite-select','sqlite'],'join-boundaries':['sqlite-select'],'window-frames':['sqlite-window'],'dates-sets':['sqlite-date','sqlite-select'],'schema-changes':['sqlite-alter','sqlite']},
 }.get(cid,{})
 for lid,refs in specific.items():combined[lid]['sources']=refs
 for (lid,index),completion in repairs(cid).items():
     completion['goal']='Repair the code by filling ____. '+completion['explanation']+' Target result: '+completion['answer']+'.'
     combined[lid]['scenarios'][index]['completion']=completion
 # The read target is explicitly about an erased assertion, not any cast.
 if cid=='typescript':
     combined['validation']['scenarios'][2]['goal']='Assert value as string, without runtime conversion. Fill ____ with the demonstrated assertion.'
 # Preserve old section memberships only where the new dependency order agrees.
 result=[]
 for section,ids in zip(('Basics','Intermediate','Advanced'),ORDERS[cid]):
     for lid in ids.split():
         item=combined.pop(lid)
         item['section']=section
         result.append(item)
 assert not combined, (cid,list(combined))
 return sources,result
