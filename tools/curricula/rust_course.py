"""Rust Book-led curriculum: original exercises, no third-party crate tracks.
The retained foundations keep their stable IDs; new concepts get new IDs.
"""
from build import S,lesson as L,emit,source

BOOK='https://doc.rust-lang.org/book/'
CHAPTERS={
 1:('Getting started and Cargo','ch01-03-hello-cargo.html'),
 3:('Common programming concepts','ch03-00-common-programming-concepts.html'),
 4:('Ownership, references, and slices','ch04-00-understanding-ownership.html'),
 5:('Structs and methods','ch05-00-structs.html'),
 6:('Enums and pattern matching','ch06-00-enums.html'),
 7:('Packages, crates, and modules','ch07-00-managing-growing-projects-with-packages-crates-and-modules.html'),
 8:('Common collections','ch08-00-common-collections.html'),
 9:('Error handling','ch09-00-error-handling.html'),
 10:('Generics, traits, and lifetimes','ch10-00-generics.html'),
 11:('Automated tests','ch11-00-testing.html'),
 12:('A command-line I/O project','ch12-00-an-io-project.html'),
 13:('Closures and iterators','ch13-00-functional-features.html'),
 14:('Cargo and crates.io','ch14-00-more-about-cargo.html'),
 15:('Smart pointers','ch15-00-smart-pointers.html'),
 16:('Fearless concurrency','ch16-00-concurrency.html'),
 17:('Async, await, futures, and streams','ch17-00-async-await.html'),
 18:('Object-oriented design and trait objects','ch18-00-oop.html'),
 19:('Patterns and matching','ch19-00-patterns.html'),
 20:('Advanced Rust features','ch20-00-advanced-features.html'),
}

def new_lessons():
 return [
 L('cargo','Cargo, crates, and the edit-check cycle',
 'Start a binary package with cargo new, then work in src/main.rs. Cargo.toml declares package metadata and the edition; Cargo.lock records resolved dependencies. cargo check quickly type-checks without producing the final executable; cargo run builds and runs, and cargo build --release produces an optimized build. Rust compilation and the tutor are separate: uv runs Code Lingo, while Cargo builds Rust projects. Read compiler diagnostics as feedback about contracts, not just syntax.',
 S('$ cargo ~check~','Checks the package without producing the final executable','Runs the application|Runs its tests','cargo check is the fast compile-check step in the edit cycle.','run|test','What does this terminal command do?'),
 S('$ cargo ~run~ -- ${word}','Passes ${word} as an application argument','Names a Cargo package ${word}|Runs a test called ${word}','The separator sends subsequent arguments to the program launched by cargo run.','check|clean','What happens to ${word}?'),
 S('$ cargo build ~--release~','Uses the optimized release profile','Enables test-only code|Publishes the package','--release selects the release build profile; publishing is a separate action.','--tests|--lib','What build profile is selected?'),
 S('# Cargo.toml\n[package]\nname = "${word}"\nversion = "0.1.0"\n~edition~ = "2024"','Selects Rust 2024 language-edition rules','Requires crate version 2024|Downloads every compiler version','The edition key opts this package into Rust 2024 language rules.','rust-version|license','What does the last key configure?')),
 L('bindings','Immutability, mutability, and shadowing',
 'Rust bindings are immutable unless declared mut. Mutation changes a value without changing its type. A second let shadows a binding and may introduce a different type; this is useful when turning input text into a parsed value. const items need explicit types and constant expressions. Prefer immutable bindings by default and introduce mut where state really changes.',
 S('let ~mut~ retries=${n}; retries+=1; println!("{retries}");','${next}','Compile error|${n}','mut permits updating the integer binding in place.','const|ref'),
 S('let name="${word}"; ~let~ name=name.len(); println!("{name}");','${length}','Compile error|${word}','A new let shadows the string binding with a usize length.','const|mut'),
 S('let limit=${n}; ~limit=${m};~ println!("{limit}");','Compile error: immutable binding','${m}|${n}','Assigning to an existing immutable binding is rejected; use mut for reassignment.','let limit=${m};|let limit=${n};','What does the compiler report?'),
 S('const LIMIT: ~usize~=${n}; let slots=[0u8;LIMIT]; println!("{}",slots.len());','${n}','Compile error|0','Array lengths use usize; a const can supply this compile-time length.','String|bool')),
 L('types','Types, expressions, and explicit conversion',
 'Integer widths and signedness are part of the type: u8 differs from i32 and usize. Rust does not silently coerce arbitrary numeric types. An as cast explicitly changes numeric representation; checked methods let callers handle overflow. A block with no final semicolon yields its final expression, while a trailing semicolon discards that value and yields unit (). char is a Unicode scalar value, not a one-byte integer.',
 S('let size:u8=${n}; let count=~usize::from(size)~; println!("{}",count+1);','${next}','Compile error|${n}','A lossless From conversion explicitly changes u8 into usize.','size as bool|String::from(size)'),
 S('let limit={let base=${n}; ~base+1~}; println!("{limit}");','${next}','Compile error|()','The trailing expression makes the block produce an integer value.','base+1;|()'),
 S('let n=255u8; println!("{:?}",n.~checked_add~(1));','None','Some(0)|Panics','checked_add reports overflow as None instead of depending on build-profile overflow behavior.','wrapping_add|saturating_add'),
 S('let initial:~char~=\'λ\'; println!("{}",initial.len_utf8());','2','1|Compile error','char stores a Unicode scalar; this scalar takes two UTF-8 bytes when encoded.','u8|&str')),
 L('models','Structs and enums as domain models',
 'Model named fields with structs and alternative states with enums. Enum variants can carry different payload types, so callers must handle the possible states explicitly instead of juggling flags and nulls. Method receivers reveal ownership: &self reads, &mut self mutates, and self consumes. Struct-update syntax can move owned fields from the source; matching by reference lets code inspect an enum without consuming its payload.',
 S('struct Config {limit:usize}\nimpl Config {fn increase(~&mut self~){self.limit+=1;}}\nlet mut cfg=Config{limit:${n}}; cfg.increase(); println!("{}",cfg.limit);','${next}','${n}|Compile error','A mutable receiver lets the method update the configuration field.','&self|self'),
 S('enum State {Ready(String),Idle}\nlet state=State::Ready(String::from("${word}"));\nif let State::Ready(name)=~&state~ {println!("{name}");}\nif let State::Ready(name)=state {println!("{name}");}','${word}\n${word}','Compile error|${word}','Borrowing for the first match keeps the owned payload available for the second match.','state|&mut state'),
 S('struct Config {name:String,limit:usize}\nlet old=Config{name:String::from("${word}"),limit:1};\nlet new=Config{limit:${n},~..old~}; println!("{} {}",new.name,new.limit);','${word} ${n}','Compile error|${word} 1','Struct update moves the remaining owned name field from old into new.','..Default::default()|old'),
 S('enum Command {Print{copies:usize},Quit}\nlet cmd=Command::Print{copies:${n}};\nlet copies=match cmd {~Command::Print{copies}~=>copies,Command::Quit=>0}; println!("{copies}");','${n}','0|Compile error','The struct-like enum pattern binds the copies payload.','Command::Print{copies:_}|Command::Quit')),
 L('patterns','Destructuring, guards, and let-else',
 'Patterns describe shapes and bind values. A match must cover all possibilities; guards add a condition after a pattern. let-else is useful for early return on missing or invalid data, and its else branch must diverge. .. ignores remaining fields; _ ignores a value without naming it. A binding such as _name is still a real binding and can move an owned value.',
 S('fn size(value:Option<usize>)->usize {let ~Some(n)~=value else{return 0;}; n}\nprintln!("{}",size(Some(${n})));','${n}','0|Compile error','let-else extracts Some while returning early on None.','None|Ok(n)'),
 S('let n=Some(${n}); let label=match n {Some(x) ~if x>0~=>"positive",_=>"other"}; println!("{label}");','positive','other|Compile error','The guard restricts the Some arm to positive payloads.','if x<0|if x==0'),
 S('let (first,~..~)=("${word}",${n},true); println!("{first}");','${word}','Compile error|${n}','The rest pattern ignores the remaining tuple fields.','_|rest'),
 S('let text=Some(String::from("${word}"));\nif let Some(~_~)=text {}\nprintln!("{}",text.unwrap());','${word}','Compile error: moved value|Panics','The wildcard ignores the payload without moving it into a binding.','_name|name')),
 L('generics','Generic APIs and trait bounds',
 'A generic type parameter represents a caller-chosen type; trait bounds specify the operations the implementation may use. Monomorphization generates code for concrete generic uses. Prefer useful bounds to unnecessary cloning or concrete types. impl Trait in a return position hides one concrete implementation type, rather than accepting unrelated return types across branches. A where clause keeps larger contracts readable.',
 S('fn copy_value<T:~Copy~>(value:T)->(T,T){(value,value)}\nprintln!("{:?}",copy_value(${n}));','(${n}, ${n})','Compile error|(${n}, 0)','Copy permits duplicating this generic value without moving it away on first use.','Clone|Default'),
 S('fn render<T>(value:T)->String ~where T:std::fmt::Display~ {format!("{value}")}\nprintln!("{}",render(${n}));','${n}','Compile error|Empty string','Display supplies the formatting capability used by this generic function.','where T:Clone|where T:Copy'),
 S('fn values()->~impl Iterator<Item=i32>~ {(1..3).map(|x|x+${n})}\nprintln!("{}",values().next().unwrap());','${next}','${n}|Compile error','The opaque return type exposes Iterator behavior with i32 items.','Iterator<Item=i32>|dyn Iterator<Item=i32>'),
 S('struct Label<T>{value:T}\nlet item=~Label{value:"${word}"}~; println!("{}",item.value);','${word}','Compile error|Empty string','The initializer infers the generic field type as a string slice.','Label::<i32>{value:"${word}"}|Label{value:0}')),
 L('lifetimes','Borrowed APIs and lifetime relationships',
 'Lifetime annotations relate borrows; they never extend the lifetime of storage. Elision covers a single borrowed input and many &self methods. With multiple borrowed inputs, specify which input the returned borrow depends on. A struct containing a reference needs a lifetime parameter. Returning an owned String is often simpler when the function constructs new text; use static only for data that can really live for the entire program.',
 S('fn label<\'a>(text:~&\'a str~,ignored:&str)->&\'a str{text}\nprintln!("{}",label("${word}","other"));','${word}','Compile error|other','The return lifetime is tied only to text, not the unrelated ignored input.','&str|&\'static str'),
 S('struct View<\'a>{text:~&\'a str~}\nlet name=String::from("${word}"); let view=View{text:&name}; println!("{}",view.text);','${word}','Compile error|An address','The lifetime parameter links the view to the borrowed string storage.','&str|String'),
 S('fn make()->~String~ {format!("${word}")}\nprintln!("{}",make());','${word}','Compile error|An address','Returning owned text transfers it to the caller rather than borrowing a local temporary.','&str|&\'static str'),
 S('let result; {let text=String::from("${word}"); result=~&text~;} println!("{result}");','Compile error: borrowed value does not live long enough','${word}|Panics','The local String is dropped before result is used; an annotation cannot extend its storage lifetime.','text|text.clone()','Why is this use of result rejected?')),
 L('testing','Unit tests, integration tests, and documentation',
 'Rust safety checks do not prove business logic. cargo test compiles and runs tests. Mark unit tests with #[test] and usually group them in a #[cfg(test)] module that can access its parent module. Integration tests under tests/ use the library public API as external clients. Documentation examples can be tested too. assert_eq! compares values; should_panic checks an expected panic rather than catching every failure silently.',
 S('#[~test~]\nfn increments(){assert_eq!(${n}+1,${next});}','A passing test discovered by cargo test','A main program|A test ignored by default','The test attribute registers this function with the Rust test harness.','ignore|inline','How is this function used?'),
 S('#[test]\n#[~should_panic~(expected="invalid")]\nfn rejects(){panic!("invalid input");}','The test passes','The test necessarily fails|The test is not run','The expected panic message satisfies this test contract.','cfg|allow','What is the test result?'),
 S('# File tree\nsrc/lib.rs\n~tests~/public_api.rs','An integration test crate using the library public API','A private unit-test module|An executable example only','Cargo treats Rust files in tests as integration-test crates.','examples|benches','What kind of test is public_api.rs?'),
 S('#[~cfg(test)~]\nmod tests {use super::*; #[test] fn sane(){assert!(true);}}','Compiles this module only for test configurations','Runs every test in release builds|Publishes the module API','cfg(test) excludes these test helpers from normal library builds.','inline|allow(dead_code)','What does the outer attribute do?')),
 L('workspaces','Cargo profiles, workspaces, and public docs',
 'Cargo workspaces coordinate related packages with shared dependency resolution and a shared target directory. Keep library logic separate from executable entry points so it can be tested and reused. Build profiles tune optimization and debugging rather than changing the ownership rules. cargo doc renders API documentation and its examples. Publishing is a separate, deliberate operation; these exercises only read commands and manifests.',
 S('# Cargo.toml\n[~workspace~]\nmembers=["core","cli"]\nresolver="3"','Groups core and cli as workspace member packages','Combines both into a single source file|Publishes both packages','A workspace groups packages under shared Cargo coordination.','package|dependencies','What does this manifest establish?'),
 S('$ cargo test ~--workspace~','Tests all workspace members','Tests only the current binary|Publishes every member','--workspace selects all workspace member packages for testing.','--lib|--doc','Which packages are selected?'),
 S('$ cargo ~doc~ --no-deps','Builds this package API documentation without dependency docs','Runs the application|Publishes the package','cargo doc generates API reference pages from source documentation.','build|publish','What does this command generate?'),
 S('# Cargo.toml\n[profile.release]\n~opt-level~ = 3','Requests release optimization level 3','Sets the Rust edition to 3|Allows three data races','The release profile controls optimization settings while Rust type rules still apply.','edition|panic','What does this setting control?')),
 L('smart-pointers','Box, Rc, RefCell, and Weak',
 'Box<T> owns a heap allocation. Rc<T> shares ownership on one thread; cloning Rc increases its owner count rather than cloning the payload. RefCell<T> allows interior mutation but checks borrowing at runtime and panics on conflicting borrows. Use Weak for a non-owning relationship: upgrading may fail after strong owners disappear. Reference cycles made only of strong Rc pointers can leak; neither Rc nor RefCell makes shared data thread-safe.',
 S('let value=~Box::new~(${n}); println!("{}",*value);','${n}','An address|Compile error','Box owns a heap-allocated integer and supports dereferencing to its value.','String::from|Some'),
 S('use std::rc::Rc; let a=Rc::new(${n}); let b=~Rc::clone(&a)~; println!("{}",Rc::strong_count(&a));','2','1|${n}','Cloning Rc creates another owner of the same allocation.','*a|Rc::new(*a)'),
 S('use std::cell::RefCell; let value=RefCell::new(${n});\nlet guard=value.borrow(); let _other=value.~borrow_mut()~; println!("{}",*guard);','Panics: conflicting dynamic borrows','Compile error|${n}','RefCell enforces exclusivity at runtime; the shared borrow remains active while guard is used later.','borrow()|try_borrow_mut()','What happens when obtaining _other?'),
 S('use std::rc::Rc; let owner=Rc::new(${n}); let weak=Rc::downgrade(&owner); ~drop(owner)~; println!("{}",weak.upgrade().is_none());','true','false|Compile error','A Weak reference does not keep the allocation payload alive after its final strong owner is dropped.','drop(weak.clone())|drop(0)')),
 L('threads','Threads, channels, Arc, and Mutex',
 'thread::spawn runs a closure on another thread; move transfers captured ownership, and join waits for completion. Channels transfer values between owners. Arc shares ownership across threads but does not by itself permit unsynchronized mutation; combine it with Mutex for shared mutable state. A MutexGuard unlocks on drop. Send concerns transfer between threads, while Sync concerns sharing references. Rc is not a substitute for Arc in this use.',
 S('let text=String::from("${word}"); let worker=std::thread::spawn(~move~ || text); println!("{}",worker.join().unwrap());','${word}','Compile error|An address','move gives the spawned closure ownership of text; join returns its result.','async|mut'),
 S('let (tx,rx)=std::sync::mpsc::channel(); tx.~send~(${n}).unwrap(); println!("{}",rx.recv().unwrap());','${n}','Compile error|Deadlocks','send transfers the value into the channel before this receive.','recv|try_recv'),
 S('use std::sync::{Arc,Mutex};\nlet value=Arc::new(Mutex::new(${n})); let other=Arc::clone(&value);\nstd::thread::spawn(move || {*other.~lock()~.unwrap()+=1;}).join().unwrap();\nprintln!("{}",*value.lock().unwrap());','${next}','${n}|Compile error','lock provides exclusive guarded access; join ensures the update finishes before reading.','get_mut()|into_inner()'),
 S('use std::rc::Rc; let value=Rc::new(${n});\nstd::thread::spawn(move || println!("{}",~value~)).join().unwrap();','Compile error: Rc is not Send','Prints ${n}|Always deadlocks','Rc cannot transfer its reference-counted ownership across threads; use Arc for thread-safe shared ownership.','${n}|0','Why is this thread spawn rejected?')),
 L('async','Lazy futures, await, and cancellation',
 'Calling an async function creates a Future; its body runs when that future is polled, not when it is merely created. await is a possible suspension point within an async context. An executor polls tasks; async does not automatically create an OS thread or make blocking I/O nonblocking. Rust supplies the Future protocol and syntax, but no general-purpose standard-library async runtime. These exercises use no runtime crate: distinguish future construction from execution, and reason about bodies that an executor would drive. Dropping an unpolled future drops its captured state without starting its body.',
 S('async fn work(){println!("${word}");}\nlet pending=~work()~; drop(pending); println!("done");','done','${word}\ndone|Compile error','The future is dropped before polling, so the async body never prints.','()|{println!("${word}");}'),
 S('async fn value()->i32{${n}}\nasync fn run()->i32{value()~.await~+1}','${next}','${n}|A second OS thread','await obtains the completed i32 from value before adding one.','|.unwrap()','When an executor drives run() to completion, what value does it produce?'),
 S('use std::future::Future;\nfn task()->impl Future<Output=i32>{~async~ {${n}}}','A future whose output type is i32','An i32 returned immediately|An OS thread handle','An async block creates a value implementing Future with the specified output type.','move|unsafe','What does task() return?'),
 S('async fn job(){let _value=std::fs::~read_to_string~("notes.txt");}','Can block the executor thread during the file read','Automatically performs nonblocking I/O|Creates a dedicated OS thread','Ordinary std::fs file reading remains blocking inside async code; the async keyword does not transform it.','metadata|read_dir','What execution property should a reviewer notice?')),
 L('trait-objects','Trait objects and API design',
 'Use enums for a known set of alternatives and trait objects when heterogeneous implementations need a common interface. dyn Trait dispatches through an object, often behind & or Box; generic bounds usually use static dispatch. A trait object needs a dyn-compatible trait: a method with its own unconstrained generic type parameter is a common incompatibility. Associated types let a trait describe an implementation-chosen type, as Iterator does with Item.',
 S('trait Named {fn name(&self)->&str;}\nstruct Item; impl Named for Item {fn name(&self)->&str{"${word}"}}\nlet item=Item; let named:~&dyn Named~=&item; println!("{}",named.name());','${word}','Compile error|An address','A borrowed trait object dispatches name to the concrete Item implementation.','dyn Named|&String'),
 S('trait Value {fn value(&self)->i32;}\nstruct Count; impl Value for Count {fn value(&self)->i32{${n}}}\nlet item:~Box<dyn Value>~=Box::new(Count); println!("{}",item.value());','${n}','Compile error|0','Box owns a concrete implementation while exposing its trait-object interface.','Box<Value>|dyn Value'),
 S('trait Read {type Item; fn read(&self)->Self::Item;}\nstruct Source; impl Read for Source {type Item=~i32~; fn read(&self)->Self::Item{${n}}}\nprintln!("{}",Source.read());','${n}','Compile error|0','The implementation selects i32 for the associated Item type.','String|bool'),
 S('trait Encode {fn encode<T>(&self,value:T);}\nfn use_encoder(_:~&dyn Encode~){}','Compile error: trait is not dyn-compatible','Always compiles|Panics at runtime','The generic encode method cannot be represented by this trait-object interface.','&impl Encode|&()','Why is the parameter type rejected?')),
 L('advanced-rust','Unsafe boundaries, newtypes, and macros',
 'unsafe permits specific operations such as raw-pointer dereference; it does not disable the borrow checker or prove the operation valid. Keep invariants explicit and expose safe APIs where possible. Newtypes give domain meaning to existing representations without implicit interchangeability. macro_rules! matches syntax and expands tokens; it is not a normal runtime function call. Advanced Rust is about explicit contracts and careful API boundaries, not reaching for unsafe whenever the compiler objects.',
 S('let value=${n}; let ptr=&value as *const i32; let copied=~unsafe { *ptr }~; println!("{copied}");','${n}','Compile error|An address','This raw pointer is valid, aligned, and points to a live integer; the unsafe block permits its dereference.','*ptr|ptr'),
 S('~unsafe~ {let value=${n}; let borrow=&value; value=${m}; println!("{borrow}");}','Compile error: immutable assignment','Prints ${m}|Undefined behavior automatically','unsafe does not permit assigning to an immutable binding or bypass ordinary borrow rules.','const|async','Does unsafe make this assignment valid?'),
 S('struct Retries(usize); let limit=~Retries(${n})~; println!("{}",limit.0);','${n}','Compile error|0','The newtype constructor wraps a usize as a distinct domain type.','${n}|Some(${n})'),
 S('macro_rules! wrap {($value:expr)=>{Some($value)};}\nprintln!("{:?}",~wrap!(${n})~);','Some(${n})','Compile error|${n}','The macro accepts an expression and expands to an Option constructor.','wrap(${n})|wrap![]')),
 ]

def curriculum():
    from systems import rust as foundations
    retained={l['id']:l for l in foundations() if l['id'] not in ('values','arithmetic')}
    fresh={l['id']:l for l in new_lessons()}
    def replace(lid,index,scenario,stable_id):
        scenarios=list(retained[lid]['scenarios']);scenario['id']=stable_id;scenarios[index]=scenario
        retained[lid]['scenarios']=scenarios

    replace('branches',2,S('let mut called=false; let result=false ~&&~ {called=true; true}; println!("{result} {called}");','false false','false true|true true','Short-circuiting skips the right side when the left boolean is false.','&|||'),'short-circuit')
    retained['branches']['notes']='Rust requires bool conditions, not integer truthiness. if and match are expressions that can return values; branch result types must agree. Logical && and || short-circuit, so the skipped operand produces no side effects. Exhaustive matching is introduced here with bool and later applied to domain enums.'
    replace('text',1,S('let text="λ${word}"; println!("{} {}",text.len(),text.~chars().count()~);','${unicodebytes} ${unicodechars}','${unicodechars} ${unicodechars}|${unicodebytes} ${unicodebytes}','len counts UTF-8 bytes, while chars counts Unicode scalar values; neither promises user-perceived grapheme counts.','len()|bytes().count()'),'utf8')
    replace('text',2,S('let text="${word}"; let prefix=~&text[..1]~; println!("{prefix}");','${first}','${word}|Compile error','A borrowed slice views the first byte of this ASCII word, which is a valid UTF-8 character boundary.','&text[..]|&text[1..]'),'slices')
    retained['text']['notes']='String owns UTF-8 storage; &str borrows a view and is usually the flexible choice for read-only text parameters. len counts bytes, chars iterates Unicode scalar values, and neither automatically counts grapheme clusters. Rust rejects numeric string indexing such as text[0]; a byte-range slice must start and end on UTF-8 boundaries or it panics. Use slices to inspect text without allocation and to_owned or String::from when ownership is needed.'
    replace('collections',1,S('let mut values=vec![${n},${m}]; for value in ~&mut values~ {*value+=1;} println!("{}",values[0]);','${next}','${n}|Compile error','Iterating over mutable references updates vector elements without consuming the vector.','&values|values'),'borrowed-iteration')
    replace('collections',2,S('use std::collections::HashMap; let mut counts=HashMap::new();\n*counts.entry("${word}").~or_insert~(0)+=${n}; println!("{}",counts["${word}"]);','${n}','0|Compile error','entry locates the key once; or_insert supplies a mutable reference to its existing value or a newly inserted zero.','or_default|insert'),'entry')
    replace('collections',3,S('use std::collections::HashMap; let mut names=HashMap::new(); let label=String::from("${word}");\nnames.insert(1,~label~); println!("{label}");','Compile error: label was moved','${word}|Panics','Inserting an owned String transfers it into the map, so this later use of label is invalid.','label.clone()|&label','What happens at the final print?'),'map-ownership')
    retained['collections']['notes']='Choose a tuple for fixed heterogeneous positions, a Vec for an owned sequence, and HashMap for key-value lookup. This lesson teaches their Rust APIs, not data-structure algorithms. iter borrows, iter_mut borrows mutably, and into_iter takes ownership when called on an owned vector. get returns Option for missing values. HashMap::entry supports update-or-insert without separate lookup, and insertion moves owned keys or values unless they implement Copy.'
    replace('results',1,S('fn parse_size(text:&str)->Result<usize,String>{text.parse::<usize>().~map_err~(|error|format!("invalid size: {error}"))}\nprintln!("{}",parse_size("bad").is_err());','true','false|Compile error','map_err converts the parsing error into the API error type while leaving successful values unchanged.','map|unwrap_or_else'),'map-error')
    retained['results']['notes']='Use Option for absence and Result for recoverable failure; panic indicates a violated assumption or unrecoverable path. Match errors at a boundary where the application can decide what to do. ? extracts success or returns early with a compatible error, and map_err translates error types with context. unwrap is appropriate only when the invariant justifying success is clear; replacing every error with zero can hide real problems. A main returning Result may propagate failures directly.'
    replace('io',0,S('// Assume invocation: app ${word}\nlet argument=std::env::args().~nth(1)~.unwrap(); println!("{argument}");','${word}','app|Panics','Argument zero is the executable name; nth(1) selects the first supplied argument.','nth(0)|nth(2)'),'arguments')
    replace('io',1,S('fn load(path:&str)->std::io::Result<String>{let text=std::fs::read_to_string(path)~?~; Ok(text)}\n// Caller matches load("notes.txt").','Returns Err to the caller when reading fails','Panics on every read failure|Returns an empty success value','The ? operator propagates file I/O or UTF-8 decoding failure through the Result boundary.','!|.unwrap()','How does a read failure reach the caller?'),'file-errors')
    replace('io',2,S('~eprintln!~("invalid size: ${n}");','Writes the diagnostic to stderr','Writes a success value to stdout|Sets a failure exit code by itself','eprintln separates diagnostics from normal output so command pipelines can consume stdout.','println!|format!','Where does this diagnostic go?'),'stderr')
    replace('io',3,S('use std::process::ExitCode;\nfn main()->ExitCode {let argument:Option<String>=None; if argument.is_none(){eprintln!("missing path"); return ~ExitCode::FAILURE~;} ExitCode::SUCCESS}','Reports failure through the process exit status','Reports success despite the error|Panics before returning','Return a failure ExitCode from the application boundary after reporting the missing argument.','ExitCode::SUCCESS|Default::default()','What does this main report to its caller?'),'exit-status')
    retained['io']['title']='A useful CLI: arguments, files, errors, and exit status'
    retained['io']['notes']='A small Rust command-line tool is a useful integration exercise: parse configuration from arguments, keep reusable work in library functions, and handle Result at main. std::env::args includes the executable name and assumes Unicode arguments; args_os is available for arbitrary OS strings. fs::read_to_string returns io::Result<String>, including invalid UTF-8 as an error. Print successful output to stdout, diagnostics to stderr, and communicate failure with an exit status. These examples inspect a CLI boundary without implementing a search algorithm.'

    for l in retained.values():
        l['notes']+=' Reading compiler diagnostics is part of the exercise: distinguish a rejected program from a valid program that panics or returns an error.'
    # Keep the original lesson/question IDs for unchanged learning families.
    # Changed families above get descriptive new suffixes; old attempts stay in SQLite.
    all_lessons=retained|fresh
    sections={
      'Basics':['cargo','bindings','types','functions','branches','loops','ownership','borrowing'],
      'Intermediate':['text','models','patterns','modules','collections','results','traits','generics','lifetimes'],
      'Advanced':['iterators','testing','io','workspaces','smart-pointers','threads','async','trait-objects','advanced-rust'],
    }
    refs={
      'cargo':[1],'bindings':[3],'types':[3],'functions':[3],'branches':[3],'loops':[3],
      'ownership':[4],'borrowing':[4],'text':[4,8],'models':[5,6],'patterns':[6,19],
      'modules':[7],'collections':[8],'results':[9],'traits':[5,10],'generics':[10],
      'lifetimes':[10],'iterators':[13],'testing':[11],'io':[12,9],'workspaces':[14],
      'smart-pointers':[15],'threads':[16],'async':[17],'trait-objects':[18,20],
      'advanced-rust':[20],
    }
    repairs={
      ('bindings',2):S('let ~mut~ limit=${n}; limit=${m}; println!("{limit}");','${m}','Compile error|${n}','Declare the binding mutable so the later assignment is valid.','const|ref'),
      ('ownership',0):S('let a=String::from("${word}"); let b=~a.clone()~; println!("{} {}",a,b);','${word} ${word}','Compile error|Empty string','Create an independent owned copy so both String values remain usable.','a|drop(a)'),
      ('ownership',3):S('let a=String::from("${word}"); ~drop(a.clone())~; println!("{}",a);','${word}','Compile error|Empty string','Drop an independently cloned String while preserving the original owner.','drop(a)|a.clear()'),
      ('borrowing',2):S('fn label()->~String~ {String::from("${word}")}\nprintln!("{}",label());','${word}','Compile error|An address','Return owned text so the caller receives valid storage instead of a borrow of a local.','&str|&\'static str'),
      ('collections',3):S('use std::collections::HashMap; let mut names=HashMap::new(); let label=String::from("${word}");\nnames.insert(1,~label.clone()~); println!("{label}");','${word}','Compile error|Empty string','Store an independent owned String in the map and retain the original String for later use.','label|drop(label)'),
      ('lifetimes',3):S('let result; {let text=String::from("${word}"); result=~text~;} println!("{result}");','${word}','Compile error|An address','Move ownership out of the inner block so the text remains alive for the final print.','&text|&text[..]'),
      ('smart-pointers',2):S('use std::cell::RefCell; let value=RefCell::new(${n}); let guard=value.borrow();\n~drop(guard)~; *value.borrow_mut()+=1; println!("{}",*value.borrow());','${next}','Panics|${n}','End the shared borrow before obtaining a mutable borrow, then read the updated value.','drop(&guard)|println!("{}",*guard)'),
      ('threads',3):S('use std::sync::~Arc~; let value=Arc::new(${n}); let worker=Arc::clone(&value);\nstd::thread::spawn(move || println!("{}",worker)).join().unwrap();','${n}','Compile error|Deadlocks','Share ownership of this immutable integer across threads using the thread-safe reference-counted pointer.','Rc|Mutex'),
      ('trait-objects',3):S('trait Encode {fn encode<T>(&self,value:T); }\nfn use_encoder(_:~&impl Encode~){}','Compiles with static dispatch','Needs a dyn-compatible trait|Panics','Use a generic trait bound via impl Trait so this generic-method trait need not become a trait object.','&dyn Encode|dyn Encode'),
      ('advanced-rust',1):S('let mut value=${n}; {let borrow=&value; println!("{borrow}");} value=~${m}~; println!("{value}");','${n}\n${m}','Compile error|Undefined behavior','Keep the binding mutable and finish using the shared borrow before assigning the new value; no unsafe block is needed.','${n}|0'),
    }
    for (lid,index),completion in repairs.items():
        completion['goal']='Repair the code by filling ____. '+completion['explanation']+' Target result: '+completion['answer']+'.'
        all_lessons[lid]['scenarios'][index]['completion']=completion
    from rust_depth import expand
    expand(all_lessons)
    result=[]
    for section,ids in sections.items():
        for lid in ids:
            l=all_lessons[lid];l['section']=section;l['sources']=['rust-'+str(n) for n in refs[lid]]
            l['notes']='Rust Book '+', '.join('chapter '+str(n) for n in refs[lid])+'. '+l['notes']
            for scenario in l['scenarios']:
                if 'goal' not in scenario:
                    scenario['goal']='Fill ____ to satisfy this contract: '+scenario['explanation']+' Target result: '+scenario['answer']+'.'
            result.append(l)
    # Clarify construction constraints where several snippets share an outcome.
    fresh['async']['scenarios'][3]['goal']='Fill ____ with the std::fs function that reads a file into a UTF-8 String. This remains a blocking operation even inside async.'
    fresh['lifetimes']['scenarios'][0]['bad']=['&str',"&'a mut str"]
    return result


def build():
    from build import DERIVED
    DERIVED.update(unicodebytes='len(word)+2',unicodechars='len(word)+1')
    sources=[source('rust','The Rust Programming Language',BOOK)]
    sources += [source('rust-'+str(n),'Rust Book chapter '+str(n)+': '+title,BOOK+url) for n,(title,url) in CHAPTERS.items()]
    emit('rust','Rust: ownership, systems, and useful tools',
         'Rust 1.90+ / edition 2024; standard library only. Rust snippets may omit main; commands and file names are labelled separately',
         sources,curriculum(),version='2.1')

if __name__=='__main__':build()
