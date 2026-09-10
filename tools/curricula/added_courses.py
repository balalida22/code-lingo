"""Six native tracks, authored from official language learning resources."""
from build import emit, source

TRACKS = {
 'java': ('Java: JVM applications and explicit contracts', 'Java 21+; no preview features', 'https://dev.java/learn/'),
 'go': ('Go: services, interfaces, and concurrency', 'Go 1.22+; standard library', 'https://go.dev/doc/'),
 'csharp': ('C#: types, queries, and asynchronous applications', 'C# 12 / .NET 8 or newer; standard library', 'https://learn.microsoft.com/en-us/dotnet/csharp/'),
 'bash': ('Bash: read commands before running them', 'Bash 5.2+ on a Unix-like system; not POSIX sh', 'https://www.gnu.org/software/bash/manual/'),
 'kotlin': ('Kotlin: null safety and expressive JVM code', 'Kotlin 2.x / JVM; standard library, no Android frameworks', 'https://kotlinlang.org/docs/home.html'),
 'swift': ('Swift: value semantics and safe application code', 'Swift 6 language mode; standard library and Foundation', 'https://docs.swift.org/swift-book/documentation/the-swift-programming-language/'),
}


SUPPLEMENTS = {
 'java': [('Java language and API learning paths','https://dev.java/learn/',None)],
 'go': [('Go language specification','https://go.dev/ref/spec',None),
        ('Effective Go','https://go.dev/doc/effective_go',{'methods','interfaces','errors','defer','goroutines','channels'})],
 'csharp': [('C# overview','https://learn.microsoft.com/en-us/dotnet/csharp/tour-of-csharp/overview',None),
            ('Using and disposal','https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/statements/using',{'resources','interfaces','async'})],
 'bash': [],
 'kotlin': [('Kotlin basic syntax','https://kotlinlang.org/docs/basic-syntax.html',None),
            ('Kotlin extensions','https://kotlinlang.org/docs/extensions.html',{'extensions'}),
            ('Kotlin coroutine overview','https://kotlinlang.org/docs/coroutines-overview.html',{'suspension'}),
            ('Kotlin Koans learning exercises','https://kotlinlang.org/docs/koans.html',None)],
 'swift': [('Swift Book: ARC','https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/AutomaticReferenceCounting.md',{'arc','classes','closures'})],
}


def build():
    import importlib
    for cid, (title, baseline, url) in TRACKS.items():
        lessons = importlib.import_module('track_' + cid).lessons()
        sources=[source(cid+'-official', title.split(':')[0]+' official language guide', url)]
        sources += [source(cid+'-ref-'+str(i),label,link) for i,(label,link,_) in enumerate(SUPPLEMENTS[cid])]
        for index, lesson in enumerate(lessons):
            lesson['sources']=[cid+'-official'] + [cid+'-ref-'+str(i) for i,(_,_,ids) in enumerate(SUPPLEMENTS[cid]) if ids is None or lesson['id'] in ids]
            lesson['section'] = 'Basics' if index < 6 else 'Intermediate' if index < 13 else 'Advanced'
            # Error cards lead to a valid repair instead of asking learners to
            # retype the rejected program. Stable descriptive IDs survive draws.
            for scenario in lesson['scenarios']:
                scenario['fragment'] = scenario['fragment'].strip()
                if scenario.get('completion'):
                    fixed = scenario['completion']
                    fixed['fragment'] = fixed['fragment'].strip()
                    fixed['goal'] = 'Repair ____ to meet this contract: ' + fixed['explanation'] + ' Target result: ' + fixed['answer'] + '.'
        emit(cid, title, baseline + '. Snippets may omit standard imports and entry points; file and command examples are labelled. Each snippet is independent',
             sources, lessons)
