use std::collections::BTreeMap;
use std::io::{self, Write};

fn main() {
    let mut company: BTreeMap<String, Vec<String>> = BTreeMap::new();

    loop {
        print!("Enter command: ");
        io::stdout().flush().expect("Failed to flush stdout");

        let mut input = String::new();
        io::stdin().read_line(&mut input).expect("Failed to read line");

        let parts: Vec<_> = input.trim().split_whitespace().collect();

        match parts.as_slice() {
            ["add", name, department] => add_employee(&mut company, name, department),
            ["list", department] => list_employees_in_department(&company, department),
            ["all"] => list_all_employees_sorted(&company),
            ["exit"] => break,
            _ => eprintln!("Invalid command. Try again."),
        }
    }
}

fn add_employee(company: &mut BTreeMap<String, Vec<String>>, name: &str, department: &str) {
    let employees = company.entry(department.to_string()).or_insert(Vec::new());
    employees.push(name.to_string());
}

fn list_employees_in_department(company: &BTreeMap<String, Vec<String>>, department: &str) {
    if let Some(employees) = company.get(department) {
        println!("Employees in {}:", department);
        for employee in employees {
            println!("\t{}", employee);
        }
    } else {
        eprintln!("Department '{}' does not exist.", department);
    }
}

fn list_all_employees_sorted(company: &BTreeMap<String, Vec<String>>) {
    for (department, employees) in company {
        println!("Department: {}", department);
        for employee in employees {
            println!("\tEmployee: {}", employee);
        }
    }
}