// -*- mode: c++; coding: utf-8 -*-

module ToDo {

    struct Task {
	int id;
	string title;
	string description;
	bool done;
    };

    interface List {
	string getAll();       // returns Task sequence on JSON format
	string get(int id);    // returns Task on JSON formar
	void add(Task t);
	void update(Task t);
	void delete(int id);
    };
};
