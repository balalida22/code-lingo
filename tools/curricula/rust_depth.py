"""Additional original Rust Book practice for topics needing longer lessons."""
from build import S


def expand(lessons):
    extra = {
        'borrowing': [
            S('let mut text=String::from("${word}"); let view=&text; println!("{view}");\ntext.~push_str~("!"); println!("{text}");', '${word}\n${word}!',
              'Compile error|${word}\n${word}',
              'The shared borrow is last used before mutation, so the mutable method call is allowed even within the same block.', 'clear|truncate'),
            S('let mut value=${n}; let first=&mut value; *first+=1;\nlet second=~&mut value~; *second+=1; println!("{value}");', '${plus2}',
              'Compile error|${next}',
              'The first mutable reference is no longer used when the second borrow begins. Exclusive borrows may occur sequentially.', '&value|value'),
        ],
        'lifetimes': [
            S("fn first(text:~&str~)->&str {&text[..1]}\nprintln!(\"{}\",first(\"${word}\"));", '${first}',
              'Compile error|${word}',
              'With one borrowed input, lifetime elision ties the returned slice to that input. These generated words are ASCII.', 'String|char'),
            S("fn longer<'a>(a:&'a str,b:&'a str)->~&'a str~ {if a.len()>b.len(){a}else{b}}\nprintln!(\"{}\",longer(\"${word}\",\"x\"));", '${word}',
              'x|Compile error',
              'Either input may supply the returned borrow. The shared lifetime contract limits its use to where both input borrows are valid; it does not extend storage lifetime.', "&'static str|String"),
        ],
        'smart-pointers': [
            S('use std::rc::Rc; let value=Rc::new(String::from("${word}"));\nlet alias=~Rc::clone(&value)~; println!("{}",Rc::strong_count(&value)); drop(alias);', '2',
              '1|Compile error',
              'Cloning an Rc adds a strong owner of the same allocation; it does not clone the contained String.', 'Rc::new((*value).clone())|&value'),
            S('use std::rc::Rc; let owner=Rc::new(${n}); let observer=Rc::~downgrade~(&owner);\ndrop(owner); println!("{}",observer.upgrade().is_none());', 'true',
              'false|Compile error',
              'A Weak pointer does not keep the value alive. After the last strong owner is dropped, upgrade returns None.', 'clone|new'),
        ],
        'threads': [
            S('use std::sync::Mutex; let count=Mutex::new(${n});\n{let mut guard=count.~lock().unwrap()~; *guard+=1;}\nprintln!("{}",*count.lock().unwrap());', '${next}',
              '${n}|Deadlocks',
              'The guard releases the mutex at the end of the inner block, allowing the second lock to succeed.', 'get_mut().unwrap()|into_inner().unwrap()'),
            S('use std::sync::{Arc,Mutex}; let count=Arc::new(Mutex::new(${n}));\nlet worker_count=Arc::clone(&count);\nlet worker=std::thread::spawn(move || {*worker_count.lock().unwrap()+=1;});\nworker.~join().unwrap()~; println!("{}",*count.lock().unwrap());', '${next}',
              '${n}|Compile error',
              'Arc shares ownership, Mutex guards mutation, and join waits for the worker before the final read, making the printed value deterministic.', 'thread()|is_finished()'),
        ],
    }
    for lid, scenarios in extra.items():
        for index, scenario in enumerate(scenarios, 1):
            scenario['id'] = f'depth-{index}'
        lessons[lid]['scenarios'] = list(lessons[lid]['scenarios']) + scenarios
    lessons['borrowing']['notes'] += ' A borrow can end at its last use, before the enclosing block ends; subsequent mutation or a new exclusive borrow can then be legal.'
    lessons['smart-pointers']['notes'] += ' Rc::clone shares an allocation instead of cloning its value. Weak observes without keeping the value alive, and upgrade returns None after the last strong owner is dropped.'
    lessons['threads']['notes'] += ' A MutexGuard unlocks when dropped. End its scope before locking the same mutex again, and join workers when later output depends on their completed updates.'
