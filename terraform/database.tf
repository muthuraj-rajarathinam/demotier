# DB Subnet Group
resource "aws_db_subnet_group" "db_subnets" {
  name       = "db-${var.project_name}-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

# RDS Instance
resource "aws_db_instance" "mysql" {
  identifier              = "db-${var.project_name}"
  engine                  = "mysql"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  multi_az                = true
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.db_subnets.name
  vpc_security_group_ids  = [aws_security_group.db_sg.id]
  skip_final_snapshot     = true
}
