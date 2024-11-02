let number_of_dialog_fields = 0;
let data;
let quote;
let quotes;
const runes = [
    'ᚠ', 'ᚡ', 'ᚢ', 'ᚣ', 'ᚤ', 'ᚥ', 'ᚦ', 'ᚧ', 'ᚨ', 'ᚩ', 'ᚪ', 'ᚫ', 'ᚬ', 'ᚭ', 'ᚮ', 'ᚯ',
    'ᚰ', 'ᚱ', 'ᚲ', 'ᚳ', 'ᚴ', 'ᚵ', 'ᚶ', 'ᚷ', 'ᚸ', 'ᚹ', 'ᚺ', 'ᚻ', 'ᚼ', 'ᚽ', 'ᚾ', 'ᚿ',
    'ᛀ', 'ᛁ', 'ᛂ', 'ᛃ', 'ᛄ', 'ᛅ', 'ᛆ', 'ᛇ', 'ᛈ', 'ᛉ', 'ᛊ', 'ᛋ', 'ᛌ', 'ᛍ', 'ᛎ', 'ᛏ',
    'ᛐ', 'ᛑ', 'ᛒ', 'ᛓ', 'ᛔ', 'ᛕ', 'ᛖ', 'ᛗ', 'ᛘ', 'ᛙ', 'ᛚ', 'ᛛ', 'ᛜ', 'ᛝ', 'ᛞ', 'ᛟ',
    'ᛠ', 'ᛡ', 'ᛢ', 'ᛣ', 'ᛤ', 'ᛥ', 'ᛦ', 'ᛧ', 'ᛨ', 'ᛩ', 'ᛪ', '᛫', '᛬', '᛭', 'ᛮ', 'ᛯ',
    'ᛰ'
];

const runes_sizes = {
    'ᚠ':10.5, 'ᚡ':10.5, 'ᚢ':9.5, 'ᚣ':8.3, 'ᚤ':9.5, 'ᚥ':9.8, 'ᚦ':7.6, 'ᚧ':7.6, 'ᚨ':5.9, 'ᚩ':8.4, 'ᚪ':8.4, 'ᚫ':7.5, 'ᚬ':7.6, 'ᚭ':5.9, 'ᚮ':5.9, 'ᚯ':7.6,
    'ᚰ':7.6, 'ᚱ':8.4, 'ᚲ':5.0, 'ᚳ':6.4, 'ᚴ':8.7, 'ᚵ':8.7, 'ᚶ':8.7, 'ᚷ':7.7, 'ᚸ':7.7, 'ᚹ':8.4, 'ᚺ':9.6, 'ᚻ':9.6, 'ᚼ':7.6, 'ᚽ':4.3, 'ᚾ':7.6, 'ᚿ':5.9,
    'ᛀ':7.6, 'ᛁ':4.2, 'ᛂ':4.2, 'ᛃ':8.1, 'ᛄ':5.8, 'ᛅ':7.6, 'ᛆ':5.9, 'ᛇ':7.6, 'ᛈ':8.4, 'ᛉ':8.6, 'ᛊ':6.1, 'ᛋ':9.1, 'ᛌ':4.2, 'ᛍ':4.2, 'ᛎ':7.6, 'ᛏ':7.6,
    'ᛐ':5.9, 'ᛑ':5.9, 'ᛒ':8.4, 'ᛓ':5.9, 'ᛔ':8.5, 'ᛕ':8.1, 'ᛖ':10.1, 'ᛗ':10.1, 'ᛘ':9.0, 'ᛙ':4.2, 'ᛚ':5.9, 'ᛛ':5.9, 'ᛜ':7.2, 'ᛝ':7.8, 'ᛞ':10.1, 'ᛟ':7.5,
    'ᛠ':8.9, 'ᛡ':7.6, 'ᛢ':8.9, 'ᛣ':8.6, 'ᛤ':7.7, 'ᛥ':10.1, 'ᛦ':9.0, 'ᛧ':4.2, 'ᛨ':7.6, 'ᛩ':8.4, 'ᛪ':9.7, '᛫':4.7, '᛬':3.5, '᛭':10.3, 'ᛮ':7.6, 'ᛯ':9.0,
    'ᛰ':9.1
};


function clear_input() {
    document.getElementById("explanation").value = "";
    document.getElementById("date").value = "";
}

async function add_field() {
    const container = document.getElementById("dialog");
    const line = document.createElement("tr");
    const author = document.createElement("select");
    author.className = "select";
    author.name = "author" + number_of_dialog_fields;
    author.id = "author" + number_of_dialog_fields;

    let option = document.createElement("option");
    option.value = "-------";
    option.text = "-------";
    option.className = "option";
    option.setAttribute("disabled", "");
    option.setAttribute("hidden", "");
    option.setAttribute("selected", "");
    author.options.add(option);

    if (data == null) {
        const response = await fetch('/authors', {headers: {'Content-Type': 'application/json'}});
        if (!response.ok) throw new Error(`Couldn't load authors: ${response.status}`);
        data = JSON.parse(await response.json());
    }


    for (let e of data.sort()) {
        option = document.createElement("option");
        option.value = e;
        option.text = e;
        option.className = "option";
        //option.style = "color: rgb(" + e['color'].replace(/ /g, ", ") + ");"
        author.options.add(option);
    }
    let td = document.createElement("td");
    td.appendChild(author);
    line.appendChild(td);

    const input = document.createElement("input");
    input.type = "text";
    input.className = "quote"
    input.id = "quote" + number_of_dialog_fields;
    input.name = "quote" + number_of_dialog_fields;
    input.spellcheck = "true"
    input.setAttribute("onkeypress", "click_press(event)");
    input.setAttribute("selected", "");

    td = document.createElement("td");
    td.appendChild(input);
    line.appendChild(td);
    container.appendChild(line)

    number_of_dialog_fields++;
}

function generate_quote() {
    /*
    {
      "quote": "Idioto gówniana",
      "author": "Oliwer",
      "date": "≈2014",
      "explanation": "Jeden z pierwszych wulgaryzmów stworzonych przez Oliwera"
    }
      {
      "quote": [
        "[Zuza]Robert! Za Tobą!",
        "[Robert]Co masz na myśli?"
      ],
      "author": "Zuza;Robert",
      "date": "----",
      "explanation": "----"
    }
    */
    const list = [];
    const date = new Date(document.getElementById("date").value);
    let explanation = document.getElementById("explanation").value;
    let date_string = "";

    if (isNaN(date)) {
        date_string = "----";
    }
    else {
        date_string = date.toLocaleString('default', { month: 'long' }) + " " + date.getFullYear();
    }

    if (explanation.length <= 1)
        explanation = "----";

    for (let i = 0; i < number_of_dialog_fields; i++) {
        const author = document.getElementById("author" + i);
        quote = document.getElementById("quote" + i);
        if (author.options[author.selectedIndex].text != "-------")
            list.push([author.options[author.selectedIndex].text, quote.value]);
    }
    if (list.length == 0){
        alert("Can't submit quote without author");
        clear_output();
    }
    else if (list.length == 1) {
        quote = `{\n\t"quote": "${list[0][1]}",\n\t"author": "${list[0][0]}",\n\t"date": "${date_string}",\n\t"explanation": "${explanation}"\n}`;
    } else {
        let base_quote = "";
        let authors = "";
        for (let e of list.filter(([a,q]) => a != "-------")) {
            base_quote += `\t\t"[${e[0]}]${e[1]}",\n`;
            authors += e[0] + ';';
        }
        base_quote = base_quote.substring(0, base_quote.length - 1);
        authors = authors.substring(0, authors.length - 1);

        quote = `{\n\t"quote": [\n${base_quote}\n\t],\n\t"author": "${authors}",\n\t"date": "${date_string}",\n\t"explanation": "${explanation}"\n}`;
    }
}

function click_press(event) {
    if (event.key == "Enter") {
        add_field();
        document.querySelector('[name="author' + (number_of_dialog_fields - 1) + '"]').focus();
    }
}

async function send_quote() {
    if (quote == null)
        return;
    
    try {
        //should be loaded from json?
        const response = await fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(quote),
        });
        if (response.ok)
            alert('Quote successfully Added')
        else
            alert(response.text())
    } catch (error) {
        alert(`There was an server error: ${error}`)
    }
    quote = null;
}

function generate_rune_for_background(list) {
    let delay = Math.random() * 25;
    let amount = Math.floor(Math.random() * 9) + 3;
    let x = Math.random() * 105 - 20;
    let y = Math.random() * 95;
    let size = 0;

    let rune = document.createElement("div");

    rune.className = "runes-container";

    for(let i=0; i < amount; i++){
        const character = document.createElement("div");
        let symbol = runes[Math.floor(Math.random() * runes.length)];
        size += runes_sizes[symbol];

        character.className = "rune";
        character.style = `animation-delay: ${delay+i*0.5}s`;
        character.append(symbol);
        rune.appendChild(character);
    }

    let retry_counter = 50;
    // console.log(`try have already saved ${list.length}`);
    // console.log(list.filter(e => Math.abs(e.top - y*vh/100) <= 16).length);
    // console.log(list.filter(e => Math.abs(e.top - y*vh/100) <= 16).filter(e => e.left < x*vw/100 && vw - e.right > x*vw/100).length);
    // console.log(list.filter(e => Math.abs(e.top - y*vh/100) <= 16).filter(e => e.left < x*vw/100 && vw - e.right > x*vw/100).filter(e => e.left < x*vw/100 + 8.5*amount && vw - e.right > x*vw/100 + 8.5*amount).length);
    while(list
        .filter(e => Math.abs(e.top - y*vh/100) <= 16)
        .filter(e => e.left < x*vw/100 && vw - e.right > x*vw/100)
        // .filter(e => e.left < x*vw/100 + size && vw - e.right > x*vw/100 + size)
        .length > 0 && retry_counter > 0
    ){
        x = Math.random() * 105 - 20;
        y = Math.random() * 95;
        retry_counter--;
    }

    if (retry_counter <= 0){
        x = 0;
        y = 0;
        rune = document.createElement("div");
        rune.style = `left: ${x}vw;top: ${y}vh;`;
    } else {
        rune.style = `left: ${x}vw;top: ${y}vh;animation: scrollAnimation ${size/4}s infinite linear;animation-delay: ${delay}s`;
    }

    return rune;
}

function generate_background() {
    const generated = [];
    vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
    vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

    for(let i=0; i < 200; i++){
        let e = generate_rune_for_background(generated);
        document.getElementById("background").appendChild(e);
        generated.push(e.getBoundingClientRect());
    }
}

async function add_quotes_display() {
    const response = await fetch('/quotes/nomination', {headers: {'Content-Type': 'application/json'}});
    if (!response.ok) throw new Error(`Couldn't load quotes: ${response.status}`);
    quotes = await response.json();
    let counter = 0;

    for (let i in quotes) {
        const q = quotes[i][0];
        const container = document.getElementById("base");
        const entry = document.createElement("div");
        const button_div = document.createElement("div");
        const accept = document.createElement("input");
        const discard = document.createElement("input");

        entry.className = "column_approve";

        for(let p of q.quote.split("[NEW_SENTENCE]")){
            const text = document.createElement("p");
            text.className = "text_approve";
            p = p.replace("]", ": ");
            p = p.replace("[", "");
            text.textContent = p;

            entry.appendChild(text);
        }

        //if (q.)
        const text = document.createElement("p");
        text.className = "text_approve";
        text.textContent = quotes[i][1];
        entry.appendChild(text);

        accept.className = "buttons";
        accept.type = "button";
        accept.setAttribute('onclick',`approve_quote(${q.id})`);
        accept.value = "Accept"

        discard.className = "buttons";
        discard.type = "button";
        discard.setAttribute('onclick', `discard_quote(${q.id})`);
        discard.value = "Discard"

        button_div.appendChild(accept);
        button_div.appendChild(discard);
        entry.appendChild(button_div);

        //entry.appendChild();
        container.appendChild(entry);
        counter++;
    }
}

function approve_quote(id){

}

function discard_quote(id){
    console.log(`discarded ${id}`)
}
