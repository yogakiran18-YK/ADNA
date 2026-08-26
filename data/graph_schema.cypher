// Constraints for uniqueness
CREATE CONSTRAINT course_code_unique IF NOT EXISTS FOR (c:Course) REQUIRE c.code IS UNIQUE;
CREATE CONSTRAINT skill_name_unique IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT role_title_unique IF NOT EXISTS FOR (r:JobRole) REQUIRE r.title IS UNIQUE;

// Indexes for fast lookups
CREATE INDEX student_id_index IF NOT EXISTS FOR (s:Student) ON (s.student_id);
