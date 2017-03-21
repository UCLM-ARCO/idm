// -*- mode: c++; coding: utf-8 -*-

module ToDo {

    struct Task {
	int id;
	string title;
	string description;
	bool done;
    };

    sequence<Task> TaskSeq;

    interface List {
	TaskSeq getAll();
	Task get(int id);
	void add(Task t);
	void update(Task t);
	void delete(int id);
    };
};
